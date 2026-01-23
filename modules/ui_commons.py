from PyQt5.QtWidgets import (QWidget, QPushButton, QDialog, QVBoxLayout, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QCoreApplication
from PyQt5.QtGui import QKeySequence, QPixmap, QImage

import socket
import mouse
import keyboard
from io import BytesIO

# --- STYLES ---
STYLES = """
    QWidget { background-color: #151d21; color: #d1e3ea; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
    QGroupBox { border: 1px solid #444; margin-top: 1.2em; font-weight: bold; color: #78aabc; border-radius: 4px; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; }
    QComboBox, QSpinBox, QLineEdit { background: #0f1518; color: #d1e3ea; border: 1px solid #2b3a41; padding: 4px; border-radius: 4px; }
    QPushButton { background-color: #2b3a41; color: #d1e3ea; border: 1px solid #444; padding: 8px; border-radius: 4px; font-weight: bold; }
    QPushButton:hover { background-color: #4a6069; border-color: #78aabc; }
    QPushButton:pressed { background-color: #78aabc; color: #000; }
    QPushButton:checked { background-color: #78aabc; color: #000; border-color: #fff; }
    QSlider::groove:horizontal { border: 1px solid #444; height: 8px; background: #0f1518; border-radius: 4px; }
    QSlider::handle:horizontal { background: #78aabc; border: 1px solid #78aabc; width: 18px; margin: -5px 0; border-radius: 9px; }
    QTabWidget::pane { border: 1px solid #444; }
    QTabBar::tab { background: #2b3a41; color: #888; padding: 8px 12px; }
    QTabBar::tab:selected { background: #3e5058; color: #fff; border-bottom: 2px solid #78aabc; }
"""

# --- QR CODE LOGIC ---
try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False
    print("⚠️ QR Code library not found. Install via: pip install qrcode[pil]")

def get_local_ip():
    """ Determines the local LAN IP address """
    try:
        # We connect to a public DNS to find our outbound IP (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

class QRDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mobile Hand-off")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            background-color: #151d21; color: #d1e3ea; 
            border: 1px solid #78aabc; font-family: 'Segoe UI';
        """)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        local_ip = get_local_ip()
        url = f"http://{local_ip}:5000"
        
        # Title
        lbl_title = QLabel(f"Scan to open on Mobile")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #78aabc; margin-bottom: 10px;")
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)
        
        # Image
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_img)
        
        if HAS_QR:
            try:
                # Generate QR
                qr = qrcode.QRCode(box_size=10, border=2)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert PIL to QPixmap
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                qimg = QImage.fromData(buffer.getvalue())
                pixmap = QPixmap.fromImage(qimg)
                lbl_img.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            except Exception as e:
                lbl_img.setText(f"Error generating QR:\n{e}")
        else:
            lbl_img.setText("Library 'qrcode' missing.\npip install qrcode[pil]")
            
        # Text URL Fallback
        lbl_url = QLabel(f"{url}")
        lbl_url.setStyleSheet("background: #000; padding: 5px; border-radius: 4px; font-family: Consolas; margin-top: 10px;")
        lbl_url.setAlignment(Qt.AlignCenter)
        lbl_url.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(lbl_url)


# --- WIDGETS ---

class JoyRecorder(QPushButton):
    startListening = pyqtSignal(str, str)
    cancelled = pyqtSignal()
    cleared = pyqtSignal(str, str) # New signal: action_id, mode

    def __init__(self, action_id, bind_type, current_bind):
        super().__init__("None")
        self.action_id = action_id
        self.bind_type = bind_type 
        self.update_display_text(current_bind)
        self.setCheckable(True)
        self.toggled.connect(self.on_toggle)
        self.setStyleSheet("text-align: center; color: #888;")

    def update_display_text(self, bind_list):
        label = "None"
        if bind_list:
            if self.bind_type == "main" and len(bind_list) >= 2 and bind_list[0]:
                 name = bind_list[0]; btn = bind_list[1]
                 short = name[:6] + ".." if len(name) > 6 else name
                 label = f"{short} [{btn}]"
            elif self.bind_type == "mod" and len(bind_list) >= 4 and bind_list[2]:
                 name = bind_list[2]; btn = bind_list[3]
                 short = name[:6] + ".." if len(name) > 6 else name
                 label = f"{short} [{btn}]"
        self.setText(label)

    def on_toggle(self, checked):
        if checked:
            self.setText("Press Btn (Esc to Clear)...")
            color = "#00ff00" if self.bind_type == "main" else "#00ffff"
            self.setStyleSheet(f"text-align: center; color: {color}; border: 1px solid {color};")
            self.grabKeyboard()
            self.startListening.emit(self.action_id, self.bind_type)
        else:
            self.releaseKeyboard()
            self.setStyleSheet("text-align: center; color: #888;")

    def keyPressEvent(self, event):
        if self.isChecked() and event.key() == Qt.Key_Escape:
            self.setChecked(False)
            self.cleared.emit(self.action_id, self.bind_type) # Trigger Clear
        else:
            super().keyPressEvent(event)

class AxisRecorder(QPushButton):
    startListening = pyqtSignal(str)
    cancelled = pyqtSignal()
    cleared = pyqtSignal(str)

    def __init__(self, action_id, current_bind):
        super().__init__("None")
        self.action_id = action_id
        self.update_display_text(current_bind)
        self.setCheckable(True)
        self.toggled.connect(self.on_toggle)
        self.setStyleSheet("text-align: center; color: #888;")

    def update_display_text(self, bind_list):
        # Format: [DevName, AxisIdx, Invert, Scale]
        label = "None"
        if bind_list and len(bind_list) >= 2:
             name = bind_list[0]; axis = bind_list[1]
             short = name[:6] + ".." if len(name) > 6 else name
             label = f"{short} [Ax{axis}]"
        self.setText(label)

    def on_toggle(self, checked):
        if checked:
            self.setText("Move Axis (Esc to Clear)...")
            color = "#e67e22"
            self.setStyleSheet(f"text-align: center; color: {color}; border: 1px solid {color};")
            self.grabKeyboard()
            self.startListening.emit(self.action_id)
        else:
            self.releaseKeyboard()
            self.setStyleSheet("text-align: center; color: #888;")

    def keyPressEvent(self, event):
        if self.isChecked() and event.key() == Qt.Key_Escape:
            self.setChecked(False)
            self.cleared.emit(self.action_id)
        else:
            super().keyPressEvent(event)

class HotkeyRecorder(QPushButton):
    hotkeyChanged = pyqtSignal(str)
    # Signal to bring mouse events back to the GUI thread
    mouse_detected = pyqtSignal(str)

    def __init__(self, current_hotkey):
        super().__init__(current_hotkey or "None")
        self.setCheckable(True)
        self.current_hotkey = current_hotkey
        self.toggled.connect(self.on_toggle)
        self.mouse_detected.connect(self.on_mouse_input) # Connect signal
        self.mouse_listener = None
        self.setStyleSheet("text-align: center; color: #aaa;")

    def on_toggle(self, checked):
        if checked:
            self.setText("Press Key or Click Mouse...")
            self.setStyleSheet("text-align: center; color: #f1c40f; border: 1px solid #f1c40f;")
            self.grabKeyboard() # Capture Keyboard
            
            # Capture Mouse (Global Hook)
            # We use a small delay to avoid capturing the click that pressed this button
            QTimer.singleShot(300, self.start_mouse_listener)
        else:
            self.stop_mouse_listener()
            self.releaseKeyboard()
            self.setText(self.current_hotkey or "None")
            self.setStyleSheet("text-align: center; color: #aaa;")

    def start_mouse_listener(self):
        if self.isChecked() and not self.mouse_listener:
            try:
                self.mouse_listener = mouse.hook(self.handle_global_mouse)
            except Exception as e:
                print(f"Error hooking mouse: {e}")

    def stop_mouse_listener(self):
        if self.mouse_listener:
            try:
                mouse.unhook(self.mouse_listener)
            except Exception: pass
            self.mouse_listener = None

    def handle_global_mouse(self, event):
        # Runs in background thread, must use signal
        detected = None
        
        # 1. Buttons (UP event only)
        if isinstance(event, mouse.ButtonEvent) and event.event_type == mouse.UP:
            mapping = {
                'left': 'left_click', 'right': 'right_click', 'middle': 'middle_click',
                'x': 'mouse_back', 'x2': 'mouse_fwd'
            }
            detected = mapping.get(event.button)

        # 2. Scroll
        elif isinstance(event, mouse.WheelEvent):
            if event.delta > 0: detected = "scroll_up"
            elif event.delta < 0: detected = "scroll_down"

        if detected:
            self.mouse_detected.emit(detected)

    def on_mouse_input(self, val):
        # Runs in Main GUI Thread
        self.current_hotkey = val
        self.setText(val)
        self.hotkeyChanged.emit(val)
        self.setChecked(False) # Stops recording

    def keyPressEvent(self, event):
        if not self.isChecked(): return super().keyPressEvent(event)
        
        key = event.key()
        if key == Qt.Key_Escape:
            self.current_hotkey = ""
            self.setText("None")
            self.hotkeyChanged.emit("")
            self.setChecked(False)
            return
        
        # Ignore modifier-only presses
        if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]: return
        
        mods = event.modifiers()
        parts = []
        if mods & Qt.ControlModifier: parts.append("ctrl")
        if mods & Qt.ShiftModifier: parts.append("shift")
        if mods & Qt.AltModifier: parts.append("alt")
        
        # Qt Key to String
        key_str = QKeySequence(key).toString().lower()
        parts.append(key_str)
        
        final = "+".join(parts)
        self.current_hotkey = final
        self.setText(final)
        self.hotkeyChanged.emit(final)
        self.setChecked(False)
