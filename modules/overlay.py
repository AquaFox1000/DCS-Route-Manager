import sys
import os
import json
import requests
import webbrowser
import keyboard
import mouse
import threading
import time
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, QComboBox, 
                             QSpinBox, QGroupBox, QGridLayout, QMessageBox, QInputDialog,
                             QTabWidget, QCheckBox, QScrollArea, QLineEdit, QListWidget, QListWidgetItem,
                             QDialog)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject, QRect, QTimer, QThread
from PyQt5.QtGui import QKeySequence, QIntValidator, QPixmap, QImage
import socket

# --- CONFIGURATION ---
SERVER_URL = "http://127.0.0.1:5000"
HUD_URL = f"{SERVER_URL}/hud?bg=transparent"
CONFIG_FILE = "config.json"
DATA_DIR = "DATA"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Default Hotkeys
DEFAULT_CONFIG = {
    "hotkeys": {
        "toggle_hud": "ctrl+shift+h",
        "settings": "ctrl+shift+alt+h",
        "testing": "ctrl+shift+alt+t",
        "trim_left": "ctrl+shift+left",
        "mark_target": "ctrl+shift+m",
        "debug": "ctrl+alt+m",
        "set_active_poi": "ctrl+shift+t",
        "cycle_next": "shift+alt+n",
        "cycle_prev": "ctrl+alt+n",
        "restore_route": "ctrl+alt+r",
        "engageAP": "ctrl+shift+a",
        "interact": "alt+f"
    },
    "joystick": {
        # Format: "action_id": [DevName, BtnIdx, ModDevName, ModBtnIdx]
    }
}

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
    from io import BytesIO
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

# --- UTILITIES ---
class InputBinder:
    _mouse_hooks = []

    @staticmethod
    def bind(trigger_str, callback):
        """ Binds a trigger string (key or mouse) to a callback """
        if not trigger_str: return

        trigger = trigger_str.lower().strip()
        
        # 1. Handle Mouse Binds
        mouse_map = {
            'left_click': 'left', 'right_click': 'right', 'middle_click': 'middle',
            'mouse_back': 'x', 'mouse_fwd': 'x2'
        }
        
        if trigger in mouse_map:
            # We use on_button (UP event) to avoid drag issues
            # We store the hook to clear it later if needed (though mouse lib is tricky with unhooking specific lambdas)
            # For simplicity in this script, we rely on the fact we usually clear all by restarting or we just append.
            # 'mouse' lib doesn't have a clean 'unhook_all' for buttons only, but we can hook/unhook.
            # To allow clearing, we wrap it.
            
            def safe_trigger():
                try: callback()
                except: pass

            hook = mouse.on_button(safe_trigger, buttons=mouse_map[trigger], types=mouse.UP)
            InputBinder._mouse_hooks.append(hook)
            return

        # 2. Handle Scroll Binds
        if trigger in ['scroll_up', 'scroll_down']:
            def scroll_handler(e):
                if isinstance(e, mouse.WheelEvent):
                    if trigger == 'scroll_up' and e.delta > 0: callback()
                    elif trigger == 'scroll_down' and e.delta < 0: callback()
            
            # mouse.hook returns the handler, which we can pass to unhook()
            InputBinder._mouse_hooks.append(mouse.hook(scroll_handler))
            return

        # 3. Handle Keyboard (Default)
        try:
            keyboard.add_hotkey(trigger, callback)
        except Exception:
            pass

    @staticmethod
    def clear_all():
        """ Clears all keyboard and mouse binds """
        try:
            keyboard.unhook_all()
        except: pass
        
        # Clear mouse hooks
        for h in InputBinder._mouse_hooks:
            try: mouse.unhook(h)
            except: pass
        InputBinder._mouse_hooks = []

class ConfigManager:
    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    config = DEFAULT_CONFIG.copy()
                    config["hotkeys"].update(data.get("hotkeys", {}))
                    # Ensure joystick section exists
                    config.setdefault("joystick", {})
                    config["joystick"].update(data.get("joystick", {}))
                    config.setdefault("test_ids", {})
                    config["test_ids"].update(data.get("test_ids", {}))
                    return config
            except Exception as e:
                print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

    @staticmethod
    def save(config):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

#   --- JOYSTICK SUPPORT    ---
# --- JOYSTICK WORKER ---
class JoystickWorker(QThread):
    # Signal for standard buttons (Pulse)
    button_pulse = pyqtSignal(str) 
    # Signal for switches (State Change: True=Pressed, False=Released)
    switch_change = pyqtSignal(str, bool) 
    # Signal for binding UI
    bind_detected = pyqtSignal(str, int)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        self.binding_mode = False 
        self.joysticks = {}
        try:
            pygame.init()
            pygame.joystick.init()
            self.scan_devices()
        except Exception as e:
            print(f"Joystick Init Error: {e}")

    def scan_devices(self):
        self.joysticks = {}
        count = pygame.joystick.get_count()
        print(f"🎮 Found {count} Joysticks/Controllers")
        for i in range(count):
            try:
                j = pygame.joystick.Joystick(i)
                j.init()
                self.joysticks[j.get_instance_id()] = j
                print(f"   - {j.get_name()} (ID: {j.get_instance_id()})")
            except: pass

    def run(self):
        while self.running:
            try:
                pygame.event.pump() 
                for event in pygame.event.get():
                    
                    # --- BINDING MODE (Listen only for DOWN) ---
                    if self.binding_mode:
                        if event.type == pygame.JOYBUTTONDOWN:
                            joy_obj = self.joysticks.get(event.instance_id)
                            if joy_obj:
                                self.bind_detected.emit(joy_obj.get_name(), event.button)
                                time.sleep(0.3)
                        continue

                    # --- NORMAL MODE ---
                    if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                        joy_obj = self.joysticks.get(event.instance_id)
                        if not joy_obj: continue
                        
                        # Pass True if DOWN, False if UP
                        self.check_binds(joy_obj.get_name(), event.button, event.type == pygame.JOYBUTTONDOWN)
                
                time.sleep(0.02) # 50Hz poll
            except Exception as e:
                print(f"Joy Loop Error: {e}")
                time.sleep(1)

    def check_binds(self, dev_name, btn_idx, is_pressed):
        joy_cfg = self.config.get("joystick", {})
        
        for action_name, bind_data in joy_cfg.items():
            if not bind_data or len(bind_data) < 2: continue
            
            # Data format: [MainDev, MainBtn, ModDev, ModBtn, IsSwitch]
            target_name = bind_data[0]
            target_btn = bind_data[1]
            
            # Check Match
            if target_name in dev_name and btn_idx == target_btn:
                
                # Check Modifier (Only required on Press)
                if len(bind_data) >= 4:
                    mod_name = bind_data[2]
                    mod_btn = bind_data[3]
                    # If pressing down, modifier must be held. 
                    # If releasing, we process it regardless to ensure "Off" signal is sent
                    if is_pressed and mod_name and not self.is_button_held(mod_name, mod_btn):
                        continue 

                # Check Mode (Switch vs Button)
                is_switch = False
                if len(bind_data) >= 5:
                    is_switch = bind_data[4]

                if is_switch:
                    # Switch: Emit State Change (True=On, False=Off)
                    self.switch_change.emit(action_name, is_pressed)
                else:
                    # Button: Emit Pulse only on Press
                    if is_pressed:
                        self.button_pulse.emit(action_name)

    def is_button_held(self, dev_name_substr, btn_idx):
        for j in self.joysticks.values():
            if dev_name_substr in j.get_name():
                try:
                    if j.get_button(btn_idx): return True
                except: pass
        return False

    def stop(self):
        self.running = False
        pygame.quit()

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
            self.mouse_listener = mouse.hook(self.handle_global_mouse)

    def stop_mouse_listener(self):
        if self.mouse_listener:
            mouse.unhook(self.mouse_listener)
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

# --- TABS ---
# --- CONTROLS TAB ---
class ControlsTab(QWidget):
    def __init__(self, parent_win, config, joy_worker):
        super().__init__()
        self.parent_win = parent_win
        self.config = config
        self.joy_worker = joy_worker
        self.hotkeys = self.config["hotkeys"]
        self.joy_binds = self.config["joystick"]
        
        self.joy_recorders = {} 
        self.active_action = None 
        self.active_mode = None 

        layout = QGridLayout()
        layout.setSpacing(10)
        
        layout.addWidget(QLabel("<b>Function</b>"), 0, 0)
        layout.addWidget(QLabel("<b>Keyboard</b>"), 0, 1)
        layout.addWidget(QLabel("<b>Joystick</b>"), 0, 2)
        layout.addWidget(QLabel("<b>Modifier</b>"), 0, 3)
        layout.addWidget(QLabel("<b>Switch</b>"), 0, 4) # NEW COLUMN
        
        self.row_idx = 1
        
        # --- PRESERVING YOUR BUTTONS ---
        self.add_control(layout, "Toggle Overlay", "toggle_hud")
        self.add_control(layout, "Mark Visual Target", "mark_target")
        self.add_control(layout, "Quick Trim Left", "trim_left")
        self.add_control(layout, "Open Settings", "settings")
        self.add_control(layout, "Open Debugger", "testing")
        self.add_control(layout, "Set Active Visual Target", "set_active_poi")
        self.add_control(layout, "Cycle Next WP/TGT", "cycle_next")
        self.add_control(layout, "Cycle Prev WP/TGT", "cycle_prev")
        self.add_control(layout, "Restore Nav Route", "restore_route")
        self.add_control(layout, "Engage/Disengage AP", "engageAP")

        save_btn = QPushButton("Save & Apply Controls")
        save_btn.clicked.connect(self.save_controls)
        save_btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #8fbc8f;")
        layout.addWidget(save_btn, self.row_idx, 0, 1, 5)
        
        layout.setRowStretch(self.row_idx + 1, 1)
        self.setLayout(layout)
        self.joy_worker.bind_detected.connect(self.on_joy_input)

    def add_control(self, layout, label, key_id):
        layout.addWidget(QLabel(label), self.row_idx, 0)
        
        # Keyboard
        recorder = HotkeyRecorder(self.hotkeys.get(key_id, ""))
        recorder.hotkeyChanged.connect(lambda val, k=key_id: self.update_key_config(k, val))
        layout.addWidget(recorder, self.row_idx, 1)
        
        # Joystick Logic
        curr_bind = self.joy_binds.get(key_id, [])
        
        rec_main = JoyRecorder(key_id, "main", curr_bind)
        rec_main.startListening.connect(self.enter_joy_bind_mode)
        rec_main.cancelled.connect(self.cancel_bind_mode)
        rec_main.cleared.connect(self.clear_joy_bind) # Handle Clear
        layout.addWidget(rec_main, self.row_idx, 2)
        
        rec_mod = JoyRecorder(key_id, "mod", curr_bind)
        rec_mod.startListening.connect(self.enter_joy_bind_mode)
        rec_mod.cancelled.connect(self.cancel_bind_mode)
        rec_mod.cleared.connect(self.clear_joy_bind) # Handle Clear
        layout.addWidget(rec_mod, self.row_idx, 3)
        
        # Switch Checkbox
        chk_switch = QCheckBox()
        is_switch = False
        if len(curr_bind) >= 5: is_switch = curr_bind[4]
        chk_switch.setChecked(is_switch)
        layout.addWidget(chk_switch, self.row_idx, 4)

        if key_id not in self.joy_recorders: self.joy_recorders[key_id] = {}
        self.joy_recorders[key_id]["main"] = rec_main
        self.joy_recorders[key_id]["mod"] = rec_mod
        self.joy_recorders[key_id]["switch"] = chk_switch
        
        self.row_idx += 1

    def update_key_config(self, key_id, value):
        self.hotkeys[key_id] = value

    def enter_joy_bind_mode(self, action_id, mode):
        for aid, groups in self.joy_recorders.items():
            if groups["main"].isChecked() and (aid != action_id or mode != "main"): groups["main"].setChecked(False)
            if groups["mod"].isChecked() and (aid != action_id or mode != "mod"): groups["mod"].setChecked(False)
        self.active_action = action_id
        self.active_mode = mode
        self.joy_worker.binding_mode = True

    def cancel_bind_mode(self):
        self.active_action = None
        self.active_mode = None
        self.joy_worker.binding_mode = False

    def clear_joy_bind(self, action_id, mode):
        # Triggered when ESC is pressed in JoyRecorder
        current = self.joy_binds.get(action_id, [])
        if not current: return

        if mode == "main":
            # Clearing main also clears mod usually, or we just blank it
            # Let's blank main data: index 0 and 1
            if len(current) >= 2:
                current[0] = ""
                current[1] = 0
        elif mode == "mod":
            # Blank mod data: index 2 and 3
            if len(current) >= 4:
                current[2] = ""
                current[3] = 0
        
        self.joy_binds[action_id] = current
        self.joy_recorders[action_id]["main"].update_display_text(current)
        self.joy_recorders[action_id]["mod"].update_display_text(current)

    def on_joy_input(self, dev_name, btn_idx):
        if self.active_action and self.active_mode:
            current = self.joy_binds.get(self.active_action, [])
            
            # Preserve existing switch state
            is_switch = False
            if len(current) >= 5: is_switch = current[4]

            if self.active_mode == "main":
                mod_part = current[2:4] if len(current) >= 4 else []
                new_bind = [dev_name, btn_idx] + mod_part
            else:
                main_part = current[:2] if len(current) >= 2 else ["", 0] 
                new_bind = main_part + [dev_name, btn_idx]
            
            # Re-attach switch state
            if len(new_bind) == 4: new_bind.append(is_switch)
            elif len(new_bind) == 2: new_bind = new_bind + ["", 0, is_switch]

            self.joy_binds[self.active_action] = new_bind
            self.joy_recorders[self.active_action]["main"].update_display_text(new_bind)
            self.joy_recorders[self.active_action]["mod"].update_display_text(new_bind)
            self.joy_recorders[self.active_action][self.active_mode].setChecked(False)
            self.cancel_bind_mode()

    def save_controls(self):
        # 1. Update Config Object from UI
        for action_id, groups in self.joy_recorders.items():
            is_switch = groups["switch"].isChecked()
            current = self.joy_binds.get(action_id, [])
            
            # Handle empty binds that just have a switch setting
            if not current: 
                if is_switch: current = ["", 0, "", 0, True]
                else: continue
            
            # Ensure list structure is complete [Dev, Btn, ModDev, ModBtn, Switch]
            while len(current) < 4: current.append(0)
            if len(current) == 4: current.append(is_switch)
            else: current[4] = is_switch
            
            self.joy_binds[action_id] = current

        # 2. Save to File & Apply
        ConfigManager.save(self.config)
        self.parent_win.overlay.update_global_hotkeys()
        
        # 3. Non-Blocking Visual Feedback (Replaces the Button Text)
        btn = self.sender()
        if btn:
            # Store original styles/text to restore later
            btn.setText("✔ Controls Saved!")
            # Make it bright green to indicate success
            btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #00ff00; border: 1px solid #00ff00; font-weight: bold;")
            
            # Helper to revert the button
            def restore_btn():
                btn.setText("Save & Apply Controls")
                btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #8fbc8f;")
            
            # Trigger restore after 1 seconds (1000 ms)
            QTimer.singleShot(1000, restore_btn)

class HUDTab(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.p_win = parent_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        prof_group = QGroupBox("PROFILE MANAGER")
        prof_layout = QVBoxLayout()
        self.p_win.prof_combo = QComboBox()
        self.p_win.prof_combo.activated.connect(self.p_win.change_profile)
        prof_layout.addWidget(self.p_win.prof_combo)
        
        btn_row = QHBoxLayout()
        btn_new = QPushButton("Create New"); btn_new.clicked.connect(self.p_win.new_profile)
        btn_del = QPushButton("Delete"); btn_del.clicked.connect(self.p_win.delete_profile)
        btn_del.setStyleSheet("background-color: #3a2b2b; color: #e74c3c;")
        btn_row.addWidget(btn_new); btn_row.addWidget(btn_del)
        prof_layout.addLayout(btn_row)
        prof_group.setLayout(prof_layout); layout.addWidget(prof_group)

        layout_group = QGroupBox("WINDOW POSITION & SIZE")
        layout_v = QVBoxLayout()
        self.p_win.monitor_combo = QComboBox()
        self.p_win.monitor_combo.currentIndexChanged.connect(self.p_win.snap_to_monitor)
        layout_v.addWidget(QLabel("Target Monitor:"))
        layout_v.addWidget(self.p_win.monitor_combo)
        
        grid = QGridLayout(); grid.setSpacing(10)
        def make_row(row_idx, label, attr_name, min_v, max_v):
            lbl = QLabel(label)
            slider = QSlider(Qt.Horizontal)
            spin = QSpinBox(); spin.setRange(min_v, max_v); spin.setSingleStep(1)
            setattr(self.p_win, f"slider_{attr_name}", slider)
            setattr(self.p_win, f"spin_{attr_name}", spin)
            slider.valueChanged.connect(spin.setValue)
            spin.valueChanged.connect(slider.setValue)
            spin.valueChanged.connect(self.p_win.update_geometry)
            grid.addWidget(lbl, row_idx, 0)
            grid.addWidget(slider, row_idx, 1)
            grid.addWidget(spin, row_idx, 2)

        make_row(0, "X:", "x", -99999, 99999)
        make_row(1, "Y:", "y", -99999, 99999)
        make_row(2, "W:", "w", 10, 30000)
        make_row(3, "H:", "h", 10, 30000)
        self.p_win.spin_w.valueChanged.connect(self.p_win.refresh_monitors_and_ranges)
        self.p_win.spin_h.valueChanged.connect(self.p_win.refresh_monitors_and_ranges)
        layout_v.addLayout(grid); layout_group.setLayout(layout_v); layout.addWidget(layout_group)

        appear_group = QGroupBox("HUD SETTINGS")
        appear_layout = QVBoxLayout()
        appear_layout.addWidget(QLabel("Symbology Theme:"))
        self.p_win.theme_combo = QComboBox()
        self.p_win.theme_combo.currentTextChanged.connect(self.p_win.push_settings)
        appear_layout.addWidget(self.p_win.theme_combo)
        appear_layout.addWidget(QLabel("HUD Color:"))
        self.p_win.color_combo = QComboBox()
        for name, hex_code in [("Green (Default)", "#00ff33"), ("Amber", "#ff9d00"), ("Yellow", "#ffff00"), ("Red", "#FF3333"), ("Light Blue", "#00ffff")]:
            self.p_win.color_combo.addItem(name, hex_code)
        self.p_win.color_combo.currentIndexChanged.connect(self.p_win.push_settings)
        appear_layout.addWidget(self.p_win.color_combo)
        self.p_win.lbl_bright = QLabel("Opacity: 100%")
        self.p_win.bright_slider = QSlider(Qt.Horizontal); self.p_win.bright_slider.setRange(0, 100)
        self.p_win.bright_slider.valueChanged.connect(self.p_win.push_settings)
        appear_layout.addWidget(self.p_win.lbl_bright); appear_layout.addWidget(self.p_win.bright_slider)
        self.p_win.lbl_scale = QLabel("Scale: 100%")
        self.p_win.scale_slider = QSlider(Qt.Horizontal); self.p_win.scale_slider.setRange(20, 200)
        self.p_win.scale_slider.valueChanged.connect(self.p_win.push_settings)
        appear_layout.addWidget(self.p_win.lbl_scale); appear_layout.addWidget(self.p_win.scale_slider)
        appear_group.setLayout(appear_layout); layout.addWidget(appear_group)
        self.p_win.lbl_fov = QLabel("FOV: 80°")
        self.p_win.fov_slider = QSlider(Qt.Horizontal); self.p_win.fov_slider.setRange(30, 120)
        self.p_win.fov_slider.valueChanged.connect(self.p_win.push_settings)
        appear_layout.addWidget(self.p_win.lbl_fov); appear_layout.addWidget(self.p_win.fov_slider)

        toggle_group = QGroupBox("ELEMENTS"); toggle_layout = QHBoxLayout()
        self.p_win.btn_dir = QPushButton("Flight Director"); self.p_win.btn_dir.setCheckable(True); self.p_win.btn_dir.clicked.connect(self.p_win.push_settings)
        self.p_win.btn_data = QPushButton("Nav Data"); self.p_win.btn_data.setCheckable(True); self.p_win.btn_data.clicked.connect(self.p_win.push_settings)
        toggle_layout.addWidget(self.p_win.btn_dir); toggle_layout.addWidget(self.p_win.btn_data)
        toggle_group.setLayout(toggle_layout); layout.addWidget(toggle_group)
        # --- CORRECTED BUTTON LAYOUT ---
        map_row = QHBoxLayout() # Initialize the layout first

        btn_map = QPushButton("Open Mission Map")
        btn_map.clicked.connect(lambda: webbrowser.open(SERVER_URL))        
        btn_map.setStyleSheet("height: 40px; font-size: 14px;") # Optional styling
        map_row.addWidget(btn_map)

        # QR Button
        btn_qr = QPushButton("📱")
        btn_qr.setToolTip("Mobile Hand-off (QR Code)")
        btn_qr.setFixedSize(40, 40)
        btn_qr.clicked.connect(self.show_qr_code)
        btn_qr.setStyleSheet("background-color: #2b3a41; border: 1px solid #78aabc; font-size: 18px;")
        map_row.addWidget(btn_qr)
        
        layout.addLayout(map_row)
        self.setLayout(layout)

    # --- MOVED OUTSIDE setup_ui (Dedented) ---
    def show_qr_code(self):
        dlg = QRDialog(self)
        dlg.exec_()

# --- WINDOWS ---
class TestingWindow(QWidget):
    def __init__(self, overlay_ref, config, joy_worker):
        super().__init__()
        self.overlay = overlay_ref
        self.browser = overlay_ref.browser
        self.config = config
        self.joy_worker = joy_worker
        
        self.setWindowTitle("ID Hunter: Command Tester")
        self.setGeometry(150, 150, 500, 600)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet(STYLES)

        # Main Layout
        main_layout = QVBoxLayout()
        
        # Scroll Area for the list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        self.layout = QGridLayout(container)
        self.layout.setSpacing(8)
        
        # --- HEADERS ---
        self.layout.addWidget(QLabel("<b>#</b>"), 0, 0)
        self.layout.addWidget(QLabel("<b>DCS ID</b>"), 0, 1)
        self.layout.addWidget(QLabel("<b>Keyboard</b>"), 0, 2)
        self.layout.addWidget(QLabel("<b>Joystick</b>"), 0, 3)
        
        self.row_idx = 1
        self.joy_recorders = {}
        self.id_inputs = {}
        btn_103 = QPushButton("⚡ Quick Fire ID 103")
        btn_103.setStyleSheet("background-color: #e67e22; color: #fff; font-weight: bold; margin: 10px 0;")
        # Send Press (1) and rely on Server/Lua to handle it as a pulse
        btn_103.clicked.connect(lambda: self.overlay.browser.page().runJavaScript("socket.emit('dcs_cmd', {'id': 104, 'val': 1, 'duration': 0.1})"))
        self.layout.addWidget(btn_103, self.row_idx, 0, 1, 4)
        self.row_idx += 1


        # --- SECTION 1: SINGLE PRESS (10 Rows) ---
        self.add_section_header("SINGLE PRESS TEST (Pulse)", 10)
        for i in range(1, 11):
            self.add_test_row(f"test_single_{i}", f"S-{i}", False)

        # --- SECTION 2: CONTINUOUS FIRE (4 Rows) ---
        self.add_section_header("CONTINUOUS FIRE (Hold)", 4)
        for i in range(1, 5):
            self.add_test_row(f"test_hold_{i}", f"HOLD-{i}", True)

        # Spacer & Save
        self.layout.setRowStretch(self.row_idx, 1)
        
        save_btn = QPushButton("Save & Apply Test Binds")
        save_btn.clicked.connect(self.save_test_binds)
        save_btn.setStyleSheet("margin-top: 10px; background-color: #2b4a3b; color: #8fbc8f; font-weight:bold; padding: 10px;")
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        main_layout.addWidget(save_btn)
        
        self.setLayout(main_layout)
        
        # Connect Worker
        self.joy_worker.bind_detected.connect(self.on_joy_input)

    def add_section_header(self, text, count):
        lbl = QLabel(f"{text} ({count})")
        lbl.setStyleSheet("color: #78aabc; font-weight: bold; border-bottom: 1px solid #444; margin-top: 15px; padding-bottom: 5px;")
        self.layout.addWidget(lbl, self.row_idx, 0, 1, 4)
        self.row_idx += 1

    def add_test_row(self, action_id, label_text, is_hold):
        # Label
        self.layout.addWidget(QLabel(label_text), self.row_idx, 0)
        
        # ID Input
        inp_id = QLineEdit()
        inp_id.setValidator(QIntValidator(0, 99999))
        inp_id.setPlaceholderText("ID")
        inp_id.setFixedWidth(60)
        
        # Load saved ID
        saved_id = self.config.get("test_ids", {}).get(action_id, "")
        if saved_id: inp_id.setText(str(saved_id))
        
        self.layout.addWidget(inp_id, self.row_idx, 1)
        self.id_inputs[action_id] = inp_id

        # Keyboard Bind
        hk_val = self.config["hotkeys"].get(action_id, "")
        hk_rec = HotkeyRecorder(hk_val)
        hk_rec.hotkeyChanged.connect(lambda val, k=action_id: self.update_key_config(k, val))
        self.layout.addWidget(hk_rec, self.row_idx, 2)

        # Joystick Bind
        joy_val = self.config["joystick"].get(action_id, [])
        joy_rec = JoyRecorder(action_id, "main", joy_val)
        joy_rec.startListening.connect(self.enter_joy_bind_mode)
        joy_rec.cancelled.connect(self.cancel_bind_mode)
        joy_rec.cleared.connect(self.clear_joy_bind)
        
        # Store metadata about this row (is it a hold switch?)
        joy_rec.setProperty("is_hold_row", is_hold)
        
        self.layout.addWidget(joy_rec, self.row_idx, 3)
        self.joy_recorders[action_id] = joy_rec

        self.row_idx += 1

    # --- BINDING LOGIC (Reused from ControlsTab but simplified) ---
    def update_key_config(self, key, val):
        self.config["hotkeys"][key] = val

    def enter_joy_bind_mode(self, action_id, mode):
        # Reset others
        for aid, btn in self.joy_recorders.items():
            if aid != action_id: btn.setChecked(False)
        self.active_action = action_id
        self.joy_worker.binding_mode = True

    def cancel_bind_mode(self):
        self.active_action = None
        self.joy_worker.binding_mode = False

    def clear_joy_bind(self, action_id, mode):
        # Reset to empty
        self.config["joystick"][action_id] = []
        self.joy_recorders[action_id].update_display_text([])

    def on_joy_input(self, dev_name, btn_idx):
        if hasattr(self, 'active_action') and self.active_action:
            # Determine if this row requires "Switch" logic (Hold rows)
            btn_widget = self.joy_recorders[self.active_action]
            is_hold_row = btn_widget.property("is_hold_row")
            
            # Construct bind: [Dev, Btn, ModDev, ModBtn, IsSwitch]
            # No modifier support in this simple test panel, just basic bind
            # If hold row, 5th element is True. If single, False.
            new_bind = [dev_name, btn_idx, "", 0, is_hold_row]
            
            self.config["joystick"][self.active_action] = new_bind
            btn_widget.update_display_text(new_bind)
            btn_widget.setChecked(False)
            self.cancel_bind_mode()

    def save_test_binds(self):
        # 1. Save IDs
        for action_id, inp in self.id_inputs.items():
            txt = inp.text().strip()
            if txt:
                self.config["test_ids"][action_id] = int(txt)
            else:
                self.config["test_ids"].pop(action_id, None)

        # 2. Save Config
        ConfigManager.save(self.config)
        
        # 3. Refresh Hotkeys
        self.overlay.update_global_hotkeys()
        
        # 4. Visual Feedback
        btn = self.sender()
        btn.setText("✔ Saved!")
        QTimer.singleShot(1000, lambda: btn.setText("Save & Apply Test Binds"))
class ClickableTab(QWidget):
    def __init__(self, parent_win, config, bridge):
        super().__init__()
        self.p_win = parent_win
        self.config = config
        self.bridge = bridge
        self.layout = QHBoxLayout() # Changed to Horizontal to have List | Editor
        self.setLayout(self.layout)
        
        # --- LEFT PANEL: LIST & CONFIG ---
        left_panel = QWidget(); left_layout = QVBoxLayout(); left_panel.setLayout(left_layout)
        
        # 1. ENABLE CHECKBOX
        self.chk_enable = QCheckBox("Enable Clickable Cockpit")
        self.chk_enable.setStyleSheet("font-weight: bold; font-size: 14px; color: #78aabc;")
        self.chk_enable.toggled.connect(self.toggle_clickable)
        left_layout.addWidget(self.chk_enable)
        
        # 2. MARKER KEYBIND
        kb_group = QGroupBox("CONTROLS")
        kb_layout = QGridLayout()
        kb_layout.addWidget(QLabel("Mark Point:"), 0, 0)
        self.rec_mark = HotkeyRecorder(self.config["hotkeys"].get("mark_click_point", ""))
        self.rec_mark.hotkeyChanged.connect(self.update_binding)
        kb_layout.addWidget(self.rec_mark, 0, 1)
        
        kb_layout.addWidget(QLabel("Interact:"), 1, 0)
        self.rec_interact = HotkeyRecorder(self.config["hotkeys"].get("interact", ""))
        self.rec_interact.hotkeyChanged.connect(self.update_interact_binding)
        kb_layout.addWidget(self.rec_interact, 1, 1)
        kb_group.setLayout(kb_layout)
        left_layout.addWidget(kb_group)

        # 3. DISTANCE
        dist_layout = QHBoxLayout()
        dist_layout.addWidget(QLabel("Max Dist (cm):"))
        self.spin_dist = QSpinBox(); self.spin_dist.setRange(1, 500)
        self.spin_dist.setValue(self.config.get("clickable_dist", 60)); self.spin_dist.setSuffix(" cm")
        self.spin_dist.valueChanged.connect(self.save_distance)
        dist_layout.addWidget(self.spin_dist)
        left_layout.addLayout(dist_layout)

        # 4. LIST
        left_layout.addWidget(QLabel("<b>Clickable Points:</b>"))
        self.list_points = QListWidget() 
        self.list_points.setStyleSheet("background: #0f1518; border: 1px solid #444;")
        self.list_points.itemClicked.connect(self.on_point_selected)
        left_layout.addWidget(self.list_points)
        
        self.layout.addWidget(left_panel, 33) # 1/3 width

        # --- RIGHT PANEL: EDITOR ---
        right_panel = QGroupBox("POINT EDITOR"); right_layout = QVBoxLayout(); right_panel.setLayout(right_layout)
        
        # ID / Name
        self.lbl_id = QLabel("ID: -")
        right_layout.addWidget(self.lbl_id)
        
        right_layout.addWidget(QLabel("Name:"))
        self.edit_name = QLineEdit()
        right_layout.addWidget(self.edit_name)
        
        # Action Type Selector
        right_layout.addWidget(QLabel("Action Type:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["DCS Command (ID)", "App Function"])
        self.combo_type.currentIndexChanged.connect(self.toggle_input_fields)
        right_layout.addWidget(self.combo_type)
        
        # Input: DCS Command ID
        self.group_dcs = QWidget(); l_dcs = QVBoxLayout(); l_dcs.setContentsMargins(0,0,0,0)
        self.group_dcs.setLayout(l_dcs)
        l_dcs.addWidget(QLabel("Command ID (e.g. 3001):"))
        self.spin_cmd_id = QSpinBox(); self.spin_cmd_id.setRange(0, 99999)
        l_dcs.addWidget(self.spin_cmd_id)
        right_layout.addWidget(self.group_dcs)
        
        # Input: App Function
        self.group_app = QWidget(); l_app = QVBoxLayout(); l_app.setContentsMargins(0,0,0,0)
        self.group_app.setLayout(l_app)
        l_app.addWidget(QLabel("Select Function:"))
        self.combo_app_func = QComboBox()
        # Populate with keys from config
        self.combo_app_func.addItems(sorted(self.config["hotkeys"].keys()))
        l_app.addWidget(self.combo_app_func)
        right_layout.addWidget(self.group_app)
        
        # Buttons
        self.btn_save = QPushButton("Update Point")
        self.btn_save.clicked.connect(self.save_point)
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(self.btn_save)

        self.btn_del = QPushButton("Delete Point")
        self.btn_del.clicked.connect(self.delete_point)
        self.btn_del.setStyleSheet("background-color: #c0392b; color: white; margin-top: 5px;")
        right_layout.addWidget(self.btn_del)
        
        right_layout.addStretch()
        self.layout.addWidget(right_panel, 66) # 2/3 width

        # State management
        self.current_point_data = None
        self.refresh_timer = QTimer(); self.refresh_timer.setInterval(2000); self.refresh_timer.timeout.connect(self.refresh_list)
        self.refresh_timer.start()
        
        self.group_dcs.setVisible(True)
        self.group_app.setVisible(False)
        self.right_panel = right_panel
        self.right_panel.setEnabled(False) # Disabled until selection

        self.refresh_list()

    def toggle_clickable(self, checked):
        self.p_win.browser.page().runJavaScript(f"socket.emit('toggle_clickable', {{'state': {str(checked).lower()}}})")

    def update_binding(self, val): self.config["hotkeys"]["mark_click_point"] = val; ConfigManager.save(self.config); self.p_win.overlay.update_global_hotkeys()
    def update_interact_binding(self, val): self.config["hotkeys"]["interact"] = val; ConfigManager.save(self.config); self.p_win.overlay.update_global_hotkeys()
    def save_distance(self, val): self.config["clickable_dist"] = val; ConfigManager.save(self.config)

    def toggle_input_fields(self):
        is_dcs = (self.combo_type.currentIndex() == 0)
        self.group_dcs.setVisible(is_dcs)
        self.group_app.setVisible(not is_dcs)

    def refresh_list(self):
        # Don't refresh if user is editing (checking focus)
        if self.edit_name.hasFocus() or self.spin_cmd_id.hasFocus(): return
        
        try:
            resp = requests.get(f"{SERVER_URL}/api/clickable_points", timeout=0.5)
            if resp.status_code == 200:
                data = resp.json()
                current_row = self.list_points.currentRow()
                self.list_points.clear()
                for p in data:
                    name = p.get('name', 'Unknown')
                    item = QListWidgetItem(f"{name}")
                    # Store full object in item data
                    item.setData(Qt.UserRole, p) 
                    self.list_points.addItem(item)
                
                if current_row >= 0 and current_row < self.list_points.count():
                    self.list_points.setCurrentRow(current_row)
        except: pass

    def on_point_selected(self, item):
        self.right_panel.setEnabled(True)
        data = item.data(Qt.UserRole)
        self.current_point_data = data
        
        self.lbl_id.setText(f"ID: {data.get('id')}")
        self.edit_name.setText(data.get('name', ''))
        
        # Set Action Type
        act_type = data.get('action_type', 'dcs')
        idx = 0 if act_type == 'dcs' else 1
        self.combo_type.setCurrentIndex(idx)
        
        # Set Values
        if act_type == 'dcs':
            self.spin_cmd_id.setValue(int(data.get('action_val', 0)))
        else:
            txt = str(data.get('action_val', ''))
            cb_idx = self.combo_app_func.findText(txt)
            if cb_idx >= 0: self.combo_app_func.setCurrentIndex(cb_idx)

    def save_point(self):
        if not self.current_point_data: return
        
        new_name = self.edit_name.text()
        act_type = 'dcs' if self.combo_type.currentIndex() == 0 else 'app'
        
        val = 0
        if act_type == 'dcs':
            val = self.spin_cmd_id.value()
        else:
            val = self.combo_app_func.currentText()
            
        payload = {
            "id": self.current_point_data.get('id'),
            "name": new_name,
            "action_type": act_type,
            "action_val": val
        }
        
        self.p_win.browser.page().runJavaScript(f"socket.emit('update_clickable_point', {json.dumps(payload)})")
        
        # Feedback
        self.btn_save.setText("Saved!")
        QTimer.singleShot(1000, lambda: self.btn_save.setText("Update Point"))

    def delete_point(self):
        if not self.current_point_data: return
        pid = self.current_point_data.get('id')
        self.p_win.browser.page().runJavaScript(f"socket.emit('delete_clickable_point', {{'id': {pid}}})")
        self.right_panel.setEnabled(False)
        self.edit_name.clear()
        
class SettingsWindow(QWidget):
    def __init__(self, overlay_ref, config, joy_worker):
        super().__init__()
        self.overlay = overlay_ref
        self.browser = overlay_ref.browser
        self.config = config
        self.joy_worker = joy_worker
        self.loading = True
        
        self.geo_timer = QTimer()
        self.geo_timer.setSingleShot(True)
        self.geo_timer.setInterval(200)
        self.geo_timer.timeout.connect(self.push_settings)

        self.setWindowTitle("HUD Settings")
        self.setGeometry(100, 100, 550, 750)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet(STYLES)
        
        self.tabs = QTabWidget()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.tabs)

        self.tab_hud = HUDTab(self)
        self.tabs.addTab(self.tab_hud, "HUD Display")

        self.tab_controls = ControlsTab(self, self.config, self.joy_worker)
        self.tabs.addTab(self.tab_controls, "Controls")

        self.tab_clickable = ClickableTab(self, self.config, self.overlay.bridge)
        self.tabs.addTab(self.tab_clickable, "Clickable Cockpit")
        
        self.load_server_data()
        self.refresh_monitors_and_ranges() 
        self.loading = False

    def showEvent(self, event):
        self.refresh_monitors_and_ranges()
        self.refresh_hud_profiles()
        self.load_server_data()
        super().showEvent(event)

    def refresh_hud_profiles(self):
        try:
            resp = requests.get(f"{SERVER_URL}/api/hud_profiles", timeout=1)
            if resp.status_code == 200:
                profiles = resp.json(); current = self.theme_combo.currentText(); self.theme_combo.blockSignals(True); self.theme_combo.clear(); self.theme_combo.addItems(profiles)
                idx = self.theme_combo.findText(current); self.theme_combo.setCurrentIndex(idx if idx >= 0 else 0); self.theme_combo.blockSignals(False)
        except: pass
    
    def refresh_monitors_and_ranges(self):
        self.screens = QApplication.screens(); self.monitor_combo.blockSignals(True); curr = self.monitor_combo.currentIndex(); self.monitor_combo.clear(); total_rect = QRect()
        for i, s in enumerate(self.screens): self.monitor_combo.addItem(f"Monitor {i+1} ({s.geometry().width()}x{s.geometry().height()})"); total_rect = total_rect.united(s.geometry())
        if curr >= 0: self.monitor_combo.setCurrentIndex(curr)
        self.monitor_combo.blockSignals(False)
        pad = 500
        self.slider_x.setRange(total_rect.left()-pad, total_rect.right()); self.spin_x.setRange(total_rect.left()-pad, total_rect.right())
        self.slider_y.setRange(total_rect.top()-pad, total_rect.bottom()); self.spin_y.setRange(total_rect.top()-pad, total_rect.bottom())
        self.spin_w.setRange(10, total_rect.width()); self.spin_h.setRange(10, total_rect.height())
        self.slider_w.setRange(10, total_rect.width() + pad); self.slider_h.setRange(10, total_rect.height() + pad)

    def snap_to_monitor(self, index):
        if self.loading or index < 0 or index >= len(self.screens): return
        geo = self.screens[index].geometry(); self.loading = True; self.spin_x.setValue(geo.x()); self.spin_y.setValue(geo.y()); self.spin_w.setValue(geo.width()); self.spin_h.setValue(geo.height()); self.loading = False; self.update_geometry()

    def update_geometry(self):
        if self.loading: return
        self.overlay.setGeometry(self.spin_x.value(), self.spin_y.value(), self.spin_w.value(), self.spin_h.value())
        self.geo_timer.start()

    def new_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Profile Name:")
        if ok and name: 
            try: requests.post(f"{SERVER_URL}/api/profiles/create", json={"name": name}); self.load_server_data()
            except: pass
    def delete_profile(self):
        curr = self.prof_combo.currentText()
        if curr != "Default" and QMessageBox.question(self, "Confirm", f"Delete '{curr}'?") == QMessageBox.Yes:
            try: requests.post(f"{SERVER_URL}/api/profiles/delete", json={"name": curr}); self.load_server_data()
            except: pass
    def change_profile(self):
        try: 
            resp = requests.post(f"{SERVER_URL}/api/profiles/select", json={"name": self.prof_combo.currentText()})
            if resp.status_code == 200: self.apply_ui_settings(resp.json().get("settings", {}))
        except: pass

    def load_server_data(self):
        try:
            resp = requests.get(f"{SERVER_URL}/api/settings", timeout=2)
            if resp.status_code == 200:
                data = resp.json(); self.loading = True
                
                # 1. Standard Profile Loading (Existing)
                self.prof_combo.clear()
                self.prof_combo.addItems(data.get("profiles_list", ["Default"]))
                self.prof_combo.setCurrentText(data.get("current_profile", "Default"))
                self.apply_ui_settings(data.get("settings", {}))
                
                # 2. NEW: Restore Clickable Checkbox State
                clickable_state = data.get("clickable_enabled", False)
                if hasattr(self, 'tab_clickable'):
                    # Block signals so we don't re-trigger the 'toggle' event just by loading
                    self.tab_clickable.chk_enable.blockSignals(True)
                    self.tab_clickable.chk_enable.setChecked(clickable_state)
                    self.tab_clickable.chk_enable.blockSignals(False)

                self.loading = False
        except Exception as e: 
            print(f"Load Error: {e}")

    def apply_ui_settings(self, s):
        self.loading = True
        self.spin_x.setValue(s.get("win_x", 100)); self.spin_y.setValue(s.get("win_y", 100))
        self.spin_w.setValue(s.get("win_w", 800)); self.spin_h.setValue(s.get("win_h", 600))
        self.overlay.setGeometry(s.get("win_x", 100), s.get("win_y", 100), s.get("win_w", 800), s.get("win_h", 600))
        if "theme" in s: 
            idx = self.theme_combo.findText(s["theme"]); 
            if idx >= 0: self.theme_combo.setCurrentIndex(idx)
        if "color" in s: 
            idx = self.color_combo.findData(s["color"])
            if idx >= 0: self.color_combo.setCurrentIndex(idx)
        self.bright_slider.setValue(int(s.get("brightness", 1.0)*100)); self.scale_slider.setValue(int(s.get("scale", 100)))
        self.fov_slider.setValue(int(s.get("fov", 80)))
        self.lbl_fov.setText(f"FOV: {self.fov_slider.value()}°")
        self.btn_dir.setChecked(s.get("showDirector", True)); self.btn_data.setChecked(s.get("showWpInfo", True))
        self.lbl_bright.setText(f"Opacity: {self.bright_slider.value()}%"); self.lbl_scale.setText(f"Scale: {self.scale_slider.value()}%")
        self.loading = False

    def push_settings(self):
        if self.loading: return
        self.lbl_bright.setText(f"Opacity: {self.bright_slider.value()}%"); self.lbl_scale.setText(f"Scale: {self.scale_slider.value()}%")
        self.lbl_fov.setText(f"FOV: {self.fov_slider.value()}°")
        
        payload = {
            "win_x": self.spin_x.value(), "win_y": self.spin_y.value(), "win_w": self.spin_w.value(), "win_h": self.spin_h.value(),
            "theme": self.theme_combo.currentText(), "color": self.color_combo.currentData(),
            "brightness": self.bright_slider.value() / 100.0, "scale": self.scale_slider.value(),
            "showDirector": self.btn_dir.isChecked(), "showWpInfo": self.btn_data.isChecked(),
            "fov": self.fov_slider.value()
        }
        try: self.browser.page().runJavaScript(f"socket.emit('update_settings', {json.dumps(payload)})")
        except: pass

# --- BRIDGE (Signals) ---
class HotkeyBridge(QObject):
    toggle_hud = pyqtSignal(); toggle_settings = pyqtSignal(); toggle_testing = pyqtSignal()
    trigger_trim_left = pyqtSignal(); trigger_mark = pyqtSignal(); trigger_debug = pyqtSignal()
    trigger_set_active_poi = pyqtSignal(); trigger_cycle_next = pyqtSignal(); trigger_cycle_prev = pyqtSignal(); trigger_restore_route = pyqtSignal()
    toggleAP = pyqtSignal()
    trigger_mark_click = pyqtSignal()
    trigger_interact = pyqtSignal()
    # --- NEW SIGNALS FOR SWITCHES ---
    force_hud = pyqtSignal(bool)
    force_settings = pyqtSignal(bool)
    #   --- for testing     ---
    trigger_test_single = pyqtSignal(str)      # <--- MISSING
    trigger_test_hold = pyqtSignal(str, bool)

    def button_press(self, action_name):
        if action_name == "toggle_hud": self.toggle_hud.emit()
        elif action_name == "settings": self.toggle_settings.emit()
        elif action_name == "testing": self.toggle_testing.emit()
        elif action_name == "mark_target": self.trigger_mark.emit()
        elif action_name == "trim_left": self.trigger_trim_left.emit()
        elif action_name == "debug": self.trigger_debug.emit()
        elif action_name == "set_active_poi": self.trigger_set_active_poi.emit()
        elif action_name == "cycle_next": self.trigger_cycle_next.emit()
        elif action_name == "cycle_prev": self.trigger_cycle_prev.emit()
        elif action_name == "restore_route": self.trigger_restore_route.emit()
        elif action_name == "engageAP" : self.toggleAP.emit()
        elif action_name == "mark_click_point": self.trigger_mark_click.emit()
        elif action_name == "interact": self.trigger_interact.emit()
        elif action_name.startswith("test_single_"): self.handle_test_single(action_name)


    def switch_change(self, action_name, state):
        # Force On/Off for UI
        if action_name == "toggle_hud": self.force_hud.emit(state)
        elif action_name == "settings": self.force_settings.emit(state)
        elif action_name.startswith("test_hold_"): self.handle_test_hold(action_name, state)
        # For actions, usually we only fire on "Press" (True), ignore "Release"
        elif state: self.button_press(action_name)
    def handle_test_single(self, action_name):
        # We need to look up the ID from the shared config
        # Since Bridge doesn't hold config directly, we can get it via the parent or passed reference.
        # Ideally, we pass config to Bridge or Bridge emits a signal that overlay handles.
        # Let's emit a specific signal that the Main Overlay connects to.
        self.trigger_test_single.emit(action_name)

    def handle_test_hold(self, action_name, state):
        self.trigger_test_hold.emit(action_name, state)    

# --- MAIN APP ---
class HUDOverlay(QMainWindow):
    def __init__(self, config, bridge_ref, joy_worker):
        super().__init__(); self.config = config; self.bridge = bridge_ref; self.joy_worker = joy_worker
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput); self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_NoSystemBackground)
        self.browser = QWebEngineView(); self.browser.setAttribute(Qt.WA_TranslucentBackground); self.browser.setStyleSheet("background: transparent;"); self.browser.page().setBackgroundColor(Qt.transparent); self.browser.setUrl(QUrl(HUD_URL)); self.setCentralWidget(self.browser)
        self.settings_window = SettingsWindow(self, self.config, self.joy_worker)
        self.testing_window = TestingWindow(self, self.config, self.joy_worker)
        
        # CONNECTIONS
        self.joy_worker.button_pulse.connect(self.bridge.button_press)
        self.joy_worker.switch_change.connect(self.bridge.switch_change)

    def toggle_overlay(self): (self.hide() if self.isVisible() else self.show())
    def toggle_settings(self): (self.settings_window.hide() if self.settings_window.isVisible() else (self.settings_window.show(), self.settings_window.activateWindow()))
    def toggle_testing(self): (self.testing_window.hide() if self.testing_window.isVisible() else (self.testing_window.show(), self.testing_window.activateWindow()))

    # NEW METHODS FOR SWITCHES
    def set_overlay_visible(self, visible): (self.show() if visible else self.hide())
    def set_settings_visible(self, visible): (self.settings_window.show() if visible else self.settings_window.hide())

    def handle_remote_func(self, data):
        action = data.get('action')
        if action:
            print(f"⚡ Remote Trigger: {action}")
            # We reuse the Bridge's logic to fire the signal
            # Note: Bridge usually expects joystick input, but we can call button_press directly
            # or update switch state.
            
            # If it's a toggle (like 'toggle_hud'), we might want to just Pulse it.
            self.bridge.button_press(action)

    def update_global_hotkeys(self):
        # 1. Clear previous binds (Both Key and Mouse)
        InputBinder.clear_all()
        
        hk = self.config["hotkeys"]
        
        # Helper to bind via our new class
        def bind(name, signal):
            key = hk.get(name)
            if key and isinstance(key, str) and key.strip():
                InputBinder.bind(key, signal.emit)

        try:
            # Bind Standard Actions
            bind("toggle_hud", self.bridge.toggle_hud)
            bind("settings", self.bridge.toggle_settings)
            bind("testing", self.bridge.toggle_testing)
            bind("trim_left", self.bridge.trigger_trim_left)
            bind("mark_target", self.bridge.trigger_mark)
            bind("debug", self.bridge.trigger_debug)
            bind("set_active_poi", self.bridge.trigger_set_active_poi)
            bind("cycle_next", self.bridge.trigger_cycle_next)
            bind("cycle_prev", self.bridge.trigger_cycle_prev)
            bind("restore_route", self.bridge.trigger_restore_route)
            bind("engageAP", self.bridge.toggleAP)
            bind("mark_click_point", self.bridge.trigger_mark_click)
            bind("interact", self.bridge.trigger_interact)

            # Bind Test Panel Actions
            for action_name, key_val in hk.items():
                if not key_val or not isinstance(key_val, str) or not key_val.strip():
                    continue

                if action_name.startswith("test_single_"):
                    # Use lambda capture for the name
                    InputBinder.bind(key_val, lambda n=action_name: self.bridge.trigger_test_single.emit(n))
                
                elif action_name.startswith("test_hold_"):
                    # NOTE: Mouse buttons do not natively support "Hold" logic easily 
                    # in this simple binder (on_press/on_release). 
                    # For mouse holds, we default to just Keyboard support here or requires complex logic.
                    # We will stick to keyboard for 'Hold' actions for stability, 
                    # or standard Pulse for mouse.
                    try:
                        keyboard.on_press_key(key_val, lambda e, n=action_name: self.bridge.trigger_test_hold.emit(n, True))
                        keyboard.on_release_key(key_val, lambda e, n=action_name: self.bridge.trigger_test_hold.emit(n, False))
                    except:
                        # Fallback for mouse on hold: just trigger start (pulse behavior)
                        pass
            
            print("Input binds refreshed (Keyboard & Mouse).")
        except Exception as e: 
            print(f"Bind Error: {e}")

if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    
    # Load Config
    config = ConfigManager.load()
    
    # Init Bridge (Signals)
    bridge = HotkeyBridge()

    def execute_test_single(action_name):
        # Look up ID in config
        cmd_id = config.get("test_ids", {}).get(action_name)
        if cmd_id:
            print(f"Test Single: {cmd_id}")
            overlay.browser.page().runJavaScript(f"socket.emit('dcs_cmd', {{'id': {cmd_id}, 'val': 1, 'duration': 0.1}})")

    def execute_test_hold(action_name, state):
        cmd_id = config.get("test_ids", {}).get(action_name)
        if cmd_id:
            if state:
                # Key Pressed -> Start Loop
                print(f"Test Hold Start: {cmd_id}")
                overlay.browser.page().runJavaScript(f"socket.emit('dcs_loop_start', {{'id': {cmd_id}}})")
            else:
                # Key Released -> Stop Loop
                print(f"Test Hold Stop: {cmd_id}")
                overlay.browser.page().runJavaScript(f"socket.emit('dcs_loop_stop', {{'id': {cmd_id}}})")

    # Connect Bridge Signals
    bridge.trigger_test_single.connect(execute_test_single)
    bridge.trigger_test_hold.connect(execute_test_hold)
    
    # --- NEW: Init Joystick Worker ---
    joy_worker = JoystickWorker(config)
    joy_worker.start()
    
    # Init Overlay (Pass joy_worker)
    overlay = HUDOverlay(config, bridge, joy_worker)
    overlay.show()                  # comment out if overlay default hidden 
    
    # --- CONNECT LOGIC ---
    
    # 1. Window Toggles (Standard)
    bridge.toggle_hud.connect(overlay.toggle_overlay)
    bridge.toggle_settings.connect(overlay.toggle_settings)
    bridge.toggle_testing.connect(overlay.toggle_testing)
    
    # 2. Window Toggles (Switches/Forced State)
    bridge.force_hud.connect(overlay.set_overlay_visible)
    bridge.force_settings.connect(overlay.set_settings_visible)

    # 3. DCS & Server Commands (Using Lambdas)
    bridge.trigger_trim_left.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('dcs_cmd', {'id': 197, 'val': 1, 'duration': 0.2})"))
    bridge.trigger_mark.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('mark_look_point')"))
    bridge.trigger_debug.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('debug_dummy_marker')"))
    
    # 4. Route & POI Commands
    bridge.trigger_set_active_poi.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('activate_last_poi')"))
    bridge.trigger_cycle_next.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('cycle_wp', {'dir': 1})"))
    bridge.trigger_cycle_prev.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('cycle_wp', {'dir': -1})"))
    bridge.trigger_restore_route.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('restore_last_route')"))
    
    # 5. Nav Computer
    bridge.toggleAP.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('toggleAP')"))

    # 6. Clickable
    bridge.trigger_mark_click.connect(lambda: overlay.browser.page().runJavaScript( f"socket.emit('mark_clickable_point', {{'dist': {config.get('clickable_dist', 60)}}})" ))
    bridge.trigger_interact.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('interact_at_mouse')"))

    # Initial Hotkey Bind
    overlay.update_global_hotkeys()
    
    sys.exit(app.exec_())