import sys
import os
import json
import requests
import webbrowser
import threading
import time
import socket

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, QComboBox, 
                             QSpinBox, QGroupBox, QGridLayout, QMessageBox, QInputDialog,
                             QTabWidget, QCheckBox, QScrollArea, QLineEdit, QListWidget, QListWidgetItem,
                             QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QObject, QRect, QTimer
from PyQt5.QtGui import QIntValidator, QIcon

# --- FIX IMPORT PATH FOR RELATIVE EXECUTION ---
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NEW MODULES
from modules.input_manager import InputManager, InputBinder, OverlayConfig
from modules.ui_commons import STYLES, QRDialog, JoyRecorder, HotkeyRecorder, AxisRecorder

# --- CONFIGURATION ---
SERVER_URL = "http://127.0.0.1:5000"
HUD_URL = f"{SERVER_URL}/hud?bg=transparent"
DATA_DIR = "DATA"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# --- TABS ---

# --- CONTROLS TAB ---
class ControlsTab(QWidget):
    def __init__(self, parent_win, config, input_mgr):
        super().__init__()
        self.parent_win = parent_win
        self.config = config
        self.input_mgr = input_mgr
        self.config_handler = parent_win.config_handler # Access to save method
        
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
        layout.addWidget(QLabel("<b>Switch</b>"), 0, 4) 
        
        self.row_idx = 1
        
        # Define Actions
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
        self.add_control(layout, "Interact (Virtual Click)", "interact")

        save_btn = QPushButton("Save & Apply Controls")
        save_btn.clicked.connect(self.save_controls)
        save_btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #8fbc8f;")
        layout.addWidget(save_btn, self.row_idx, 0, 1, 5)
        
        layout.setRowStretch(self.row_idx + 1, 1)
        self.setLayout(layout)
        self.input_mgr.bind_detected.connect(self.on_joy_input)

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
        rec_main.cleared.connect(self.clear_joy_bind) 
        layout.addWidget(rec_main, self.row_idx, 2)
        
        rec_mod = JoyRecorder(key_id, "mod", curr_bind)
        rec_mod.startListening.connect(self.enter_joy_bind_mode)
        rec_mod.cancelled.connect(self.cancel_bind_mode)
        rec_mod.cleared.connect(self.clear_joy_bind) 
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
        self.input_mgr.binding_mode = True

    def cancel_bind_mode(self):
        self.active_action = None
        self.active_mode = None
        self.input_mgr.binding_mode = False

    def clear_joy_bind(self, action_id, mode):
        current = self.joy_binds.get(action_id, [])
        if not current: return

        if mode == "main":
            if len(current) >= 2:
                current[0] = ""
                current[1] = 0
        elif mode == "mod":
            if len(current) >= 4:
                current[2] = ""
                current[3] = 0
        
        self.joy_binds[action_id] = current
        self.joy_recorders[action_id]["main"].update_display_text(current)
        self.joy_recorders[action_id]["mod"].update_display_text(current)

    def on_joy_input(self, dev_name, btn_idx):
        if self.active_action and self.active_mode:
            current = self.joy_binds.get(self.active_action, [])
            
            is_switch = False
            if len(current) >= 5: is_switch = current[4]

            if self.active_mode == "main":
                mod_part = current[2:4] if len(current) >= 4 else []
                new_bind = [dev_name, btn_idx] + mod_part
            else:
                main_part = current[:2] if len(current) >= 2 else ["", 0] 
                new_bind = main_part + [dev_name, btn_idx]
            
            if len(new_bind) == 4: new_bind.append(is_switch)
            elif len(new_bind) == 2: new_bind = new_bind + ["", 0, is_switch]

            self.joy_binds[self.active_action] = new_bind
            self.joy_recorders[self.active_action]["main"].update_display_text(new_bind)
            self.joy_recorders[self.active_action]["mod"].update_display_text(new_bind)
            self.joy_recorders[self.active_action][self.active_mode].setChecked(False)
            self.cancel_bind_mode()

    def save_controls(self):
        for action_id, groups in self.joy_recorders.items():
            is_switch = groups["switch"].isChecked()
            current = self.joy_binds.get(action_id, [])
            
            if not current: 
                if is_switch: current = ["", 0, "", 0, True]
                else: continue
            
            while len(current) < 4: current.append(0)
            if len(current) == 4: current.append(is_switch)
            else: current[4] = is_switch
            
            self.joy_binds[action_id] = current

        self.config_handler.save(self.config)
        self.parent_win.overlay.update_global_hotkeys()
        
        btn = self.sender()
        if btn:
            btn.setText("✔ Controls Saved!")
            btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #00ff00; border: 1px solid #00ff00; font-weight: bold;")
            QTimer.singleShot(1000, lambda: (btn.setText("Save & Apply Controls"), btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #8fbc8f;")))


# --- POINTER TAB ---
class PointerTab(QWidget):
    def __init__(self, parent_win, config, input_mgr):
        super().__init__()
        self.parent_win = parent_win
        self.config = config
        self.input_mgr = input_mgr
        self.config_handler = parent_win.config_handler
        
        self.hotkeys = self.config["hotkeys"]
        self.joy_binds = self.config["joystick"]
        self.axes_binds = self.config["axes"]
        
        self.joy_recorders = {}
        self.axis_recorders = {}
        self.active_recorder = None # For both axis and button
        
        self.setup_ui()
        self.input_mgr.bind_detected.connect(self.on_joy_input)
        self.input_mgr.axis_detected.connect(self.on_axis_input)

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 1. Activation
        grp_activ = QGroupBox("ACTIVATION")
        l_activ = QGridLayout()
        self.add_button_bind(l_activ, 0, "Toggle Pointer Mode", "pointer_toggle")
        grp_activ.setLayout(l_activ)
        layout.addWidget(grp_activ)

        # 2. Analog Movement (Axes)
        grp_analog = QGroupBox("ANALOG MOVEMENT (Joystick/Controller)")
        l_analog = QGridLayout()
        l_analog.addWidget(QLabel("<b>Axis Function</b>"), 0, 0)
        l_analog.addWidget(QLabel("<b>Bind</b>"), 0, 1)
        l_analog.addWidget(QLabel("<b>Invert</b>"), 0, 2)
        l_analog.addWidget(QLabel("<b>Sensitivity</b>"), 0, 3)
        
        self.add_axis_bind(l_analog, 1, "Pointer X (Horizontal)", "pointer_x")
        self.add_axis_bind(l_analog, 2, "Pointer Y (Vertical)", "pointer_y")
        grp_analog.setLayout(l_analog)
        layout.addWidget(grp_analog)

        # 3. Digital Movement (Buttons/Keys)
        grp_dig = QGroupBox("DIGITAL MOVEMENT (D-Pad/Keys)")
        l_dig = QGridLayout()
        self.add_button_bind(l_dig, 0, "Move Up", "pointer_up")
        self.add_button_bind(l_dig, 1, "Move Down", "pointer_down")
        self.add_button_bind(l_dig, 2, "Move Left", "pointer_left")
        self.add_button_bind(l_dig, 3, "Move Right", "pointer_right")
        
        # Digital Sensitivity
        l_dig.addWidget(QLabel("Speed/Sensitivity:"), 4, 0)
        self.slider_dig_sens = QSlider(Qt.Horizontal)
        self.slider_dig_sens.setRange(10, 500) # 10% to 500%
        self.slider_dig_sens.setValue(int(self.config.get("digital_sensitivity", 1.0) * 100))
        self.lbl_dig_sens = QLabel(f"{self.slider_dig_sens.value()}%")
        self.slider_dig_sens.valueChanged.connect(lambda v: self.lbl_dig_sens.setText(f"{v}%"))
        l_dig.addWidget(self.slider_dig_sens, 4, 1, 1, 2)
        l_dig.addWidget(self.lbl_dig_sens, 4, 3)

        grp_dig.setLayout(l_dig)
        layout.addWidget(grp_dig)

        # --- MOUSE INPUT [NEW] ---
        grp_mouse = QGroupBox("MOUSE INPUT")
        # Removing explicit setStyleSheet as STYLES is a string and applied globally
        gm_layout = QVBoxLayout()
        grp_mouse.setLayout(gm_layout)
        
        # Checkbox: Enable Mouse Control
        self.chk_mouse = QCheckBox("Enable Mouse Control")
        # Load state from config (default False to avoid interference)
        self.chk_mouse.setChecked(self.config.get("mouse_enabled", False))
        self.chk_mouse.toggled.connect(self.toggle_mouse)
        gm_layout.addWidget(self.chk_mouse)
        
        # Mode Section
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.combo_mouse_mode = QComboBox()
        self.combo_mouse_mode.addItems(["Relative (Standard)", "Absolute (Tablet)"])
        # Load mode
        curr_mode = self.config.get("mouse_mode", "rel")
        self.combo_mouse_mode.setCurrentIndex(1 if curr_mode == "abs" else 0)
        self.combo_mouse_mode.currentIndexChanged.connect(self.change_mouse_mode)
        mode_layout.addWidget(self.combo_mouse_mode)
        gm_layout.addLayout(mode_layout)

        # Mouse Sensitivity
        sens_layout = QHBoxLayout()
        sens_layout.addWidget(QLabel("Sensitivity:"))
        self.slider_mouse_sens = QSlider(Qt.Horizontal)
        self.slider_mouse_sens.setRange(10, 500)
        self.slider_mouse_sens.setValue(int(self.config.get("mouse_sensitivity", 1.0) * 100))
        self.lbl_mouse_sens = QLabel(f"{self.slider_mouse_sens.value()}%")
        self.slider_mouse_sens.valueChanged.connect(lambda v: self.lbl_mouse_sens.setText(f"{v}%"))
        sens_layout.addWidget(self.slider_mouse_sens)
        sens_layout.addWidget(self.lbl_mouse_sens)
        gm_layout.addLayout(sens_layout)

        layout.addWidget(grp_mouse)

        # Apply initial mouse state
        self.input_mgr.enable_mouse_hook(self.chk_mouse.isChecked())

        # 4. Interaction
        grp_int = QGroupBox("INTERACTION")
        l_int = QGridLayout()
        self.add_button_bind(l_int, 0, "Left Click / Interact", "pointer_click")
        # self.add_button_bind(l_int, 1, "Right Click / Context", "pointer_context") # Future
        grp_int.setLayout(l_int)
        layout.addWidget(grp_int)

        save_btn = QPushButton("Save Pointer Settings")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #8fbc8f; padding: 10px; font-weight: bold;")
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def toggle_mouse(self, checked):
        self.config["mouse_enabled"] = checked
        self.input_mgr.config["mouse_enabled"] = checked # SYNC TO INPUT MANAGER
        self.input_mgr.enable_mouse_hook(checked)
        self.config_handler.save(self.config)
        
    def change_mouse_mode(self, idx):
        mode = "abs" if idx == 1 else "rel"
        self.config["mouse_mode"] = mode
        self.input_mgr.config["mouse_mode"] = mode # SYNC TO INPUT MANAGER
        self.config_handler.save(self.config)

    def add_button_bind(self, layout, row, label, action_id):
        layout.addWidget(QLabel(label), row, 0)
        
        # Keyboard
        hk_rec = HotkeyRecorder(self.hotkeys.get(action_id, ""))
        hk_rec.hotkeyChanged.connect(lambda val, k=action_id: self.update_key_config(k, val))
        layout.addWidget(hk_rec, row, 1)
        
        # Joystick
        curr = self.joy_binds.get(action_id, [])
        j_rec = JoyRecorder(action_id, "main", curr)
        j_rec.startListening.connect(self.enter_bind_mode)
        j_rec.cancelled.connect(self.cancel_bind_mode)
        j_rec.cleared.connect(self.clear_joy_bind)
        layout.addWidget(j_rec, row, 2)
        
        self.joy_recorders[action_id] = j_rec

    def add_axis_bind(self, layout, row, label, action_id):
        layout.addWidget(QLabel(label), row, 0)
        
        curr = self.axes_binds.get(action_id, [])
        rec = AxisRecorder(action_id, curr)
        rec.startListening.connect(self.enter_bind_mode)
        rec.cancelled.connect(self.cancel_bind_mode)
        rec.cleared.connect(self.clear_axis_bind)
        layout.addWidget(rec, row, 1)
        
        # Invert
        chk = QCheckBox("Invert")
        chk.setChecked(curr[2] if len(curr) > 2 else False)
        layout.addWidget(chk, row, 2)
        
        # Scale (Sensitivity)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(1, 200)
        slider.setValue(int(curr[3] * 100) if len(curr) > 3 else 100)
        layout.addWidget(slider, row, 3)
        
        self.axis_recorders[action_id] = {"rec": rec, "invert": chk, "scale": slider}

    def update_key_config(self, key, val):
        self.hotkeys[key] = val

    def enter_bind_mode(self, action_id, mode=None):
        # Clear others
        for rec in self.joy_recorders.values():
            if rec.action_id != action_id: rec.setChecked(False)
        for d in self.axis_recorders.values():
            if d["rec"].action_id != action_id: d["rec"].setChecked(False)
            
        self.active_recorder = {"id": action_id, "mode": mode} # mode is 'main' for btn or None for axis
        self.input_mgr.binding_mode = True

    def cancel_bind_mode(self):
        self.active_recorder = None
        self.input_mgr.binding_mode = False

    def clear_joy_bind(self, action_id, mode):
        self.joy_binds[action_id] = []
        self.joy_recorders[action_id].update_display_text([])

    def clear_axis_bind(self, action_id):
        self.axes_binds[action_id] = []
        self.axis_recorders[action_id]["rec"].update_display_text([])

    def on_joy_input(self, dev_name, btn_idx):
        if not self.active_recorder or self.active_recorder.get("mode") is None: return
        
        aid = self.active_recorder["id"]
        # Basic bind: [Dev, Btn]
        new_bind = [dev_name, btn_idx]
        self.joy_binds[aid] = new_bind
        self.joy_recorders[aid].update_display_text(new_bind)
        self.joy_recorders[aid].setChecked(False)
        self.cancel_bind_mode()

    def on_axis_input(self, dev_name, axis_idx):
        if not self.active_recorder or self.active_recorder.get("mode") is not None: return
        
        aid = self.active_recorder["id"]
        # Basic bind: [Dev, Axis, Invert(False), Scale(1.0)]
        # We preserve existing config for Invert/Scale if possible, but usually binding resets it or we just take defaults
        # Let's take current UI values
        args = self.axis_recorders[aid]
        invert = args["invert"].isChecked()
        scale = args["scale"].value() / 100.0
        
        new_bind = [dev_name, axis_idx, invert, scale]
        self.axes_binds[aid] = new_bind
        
        args["rec"].update_display_text(new_bind)
        args["rec"].setChecked(False)
        self.cancel_bind_mode()

    def save_settings(self):
        # Update Axis Params (Invert/Scale) even if not rebound
        for aid, args in self.axis_recorders.items():
            curr = self.axes_binds.get(aid, [])
            if len(curr) >= 2:
                # Update Invert/Scale indices
                while len(curr) < 4: curr.append(0)
                curr[2] = args["invert"].isChecked()
                curr[3] = args["scale"].value() / 100.0
                self.axes_binds[aid] = curr

        # Save Sensitivity Settings
        self.config["digital_sensitivity"] = self.slider_dig_sens.value() / 100.0
        self.config["mouse_sensitivity"] = self.slider_mouse_sens.value() / 100.0

        # SYNC ALL TO INPUT MANAGER
        self.input_mgr.config.update(self.config)

        self.config_handler.save(self.config)
        self.parent_win.overlay.update_global_hotkeys() # Reload hotkeys
        
        # Inline Feedback
        btn = self.sender()
        if btn:
            original_text = "Save Pointer Settings"
            original_style = "margin-top: 20px; background-color: #2b4a3b; color: #8fbc8f; padding: 10px; font-weight: bold;"
            
            btn.setText("✔ Settings Saved!")
            btn.setStyleSheet("margin-top: 20px; background-color: #2b4a3b; color: #00ff00; border: 1px solid #00ff00; padding: 10px; font-weight: bold;")
            QTimer.singleShot(1000, lambda: (btn.setText(original_text), btn.setStyleSheet(original_style)))


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
        
        map_row = QHBoxLayout() 

        btn_map = QPushButton("Open Mission Map")
        btn_map.clicked.connect(lambda: webbrowser.open(SERVER_URL))        
        btn_map.setStyleSheet("height: 40px; font-size: 14px;")
        map_row.addWidget(btn_map)

        btn_qr = QPushButton("📱")
        btn_qr.setToolTip("Mobile Hand-off (QR Code)")
        btn_qr.setFixedWidth(50)
        btn_qr.clicked.connect(self.show_qr_code)
        btn_qr.setStyleSheet("height: 40px; font-size: 18px;")
        map_row.addWidget(btn_qr)
        
        layout.addLayout(map_row)
        self.setLayout(layout)

    def show_qr_code(self):
        dlg = QRDialog(self)
        dlg.exec_()


# --- WINDOWS ---
class TestingWindow(QWidget):
    def __init__(self, overlay_ref, config, input_mgr):
        super().__init__()
        self.overlay = overlay_ref
        self.browser = overlay_ref.browser
        self.config = config
        self.input_mgr = input_mgr
        self.config_handler = overlay_ref.settings_window.config_handler # Reuse handler
        
        self.setWindowTitle("ID Hunter: Command Tester")
        self.setGeometry(150, 150, 500, 600)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet(STYLES)

        main_layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        self.layout = QGridLayout(container)
        self.layout.setSpacing(8)
        
        self.layout.addWidget(QLabel("<b>#</b>"), 0, 0)
        self.layout.addWidget(QLabel("<b>DCS ID</b>"), 0, 1)
        self.layout.addWidget(QLabel("<b>Keyboard</b>"), 0, 2)
        self.layout.addWidget(QLabel("<b>Joystick</b>"), 0, 3)
        
        self.row_idx = 1
        self.joy_recorders = {}
        self.id_inputs = {}
        btn_103 = QPushButton("⚡ Quick Fire ID 103")
        btn_103.setStyleSheet("background-color: #e67e22; color: #fff; font-weight: bold; margin: 10px 0;")
        btn_103.clicked.connect(lambda: self.overlay.browser.page().runJavaScript("socket.emit('dcs_cmd', {'id': 104, 'val': 1, 'duration': 0.1})"))
        self.layout.addWidget(btn_103, self.row_idx, 0, 1, 4)
        self.row_idx += 1

        self.add_section_header("SINGLE PRESS TEST (Pulse)", 10)
        for i in range(1, 11):
            self.add_test_row(f"test_single_{i}", f"S-{i}", False)

        self.add_section_header("CONTINUOUS FIRE (Hold)", 4)
        for i in range(1, 5):
            self.add_test_row(f"test_hold_{i}", f"HOLD-{i}", True)

        self.layout.setRowStretch(self.row_idx, 1)
        
        save_btn = QPushButton("Save & Apply Test Binds")
        save_btn.clicked.connect(self.save_test_binds)
        save_btn.setStyleSheet("margin-top: 10px; background-color: #2b4a3b; color: #8fbc8f; font-weight:bold; padding: 10px;")
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        main_layout.addWidget(save_btn)
        
        self.setLayout(main_layout)
        self.input_mgr.bind_detected.connect(self.on_joy_input)

    def add_section_header(self, text, count):
        lbl = QLabel(f"{text} ({count})")
        lbl.setStyleSheet("color: #78aabc; font-weight: bold; border-bottom: 1px solid #444; margin-top: 15px; padding-bottom: 5px;")
        self.layout.addWidget(lbl, self.row_idx, 0, 1, 4)
        self.row_idx += 1

    def add_test_row(self, action_id, label_text, is_hold):
        self.layout.addWidget(QLabel(label_text), self.row_idx, 0)
        
        inp_id = QLineEdit()
        inp_id.setValidator(QIntValidator(0, 99999))
        inp_id.setPlaceholderText("ID")
        inp_id.setFixedWidth(60)
        
        saved_id = self.config.get("test_ids", {}).get(action_id, "")
        if saved_id: inp_id.setText(str(saved_id))
        
        self.layout.addWidget(inp_id, self.row_idx, 1)
        self.id_inputs[action_id] = inp_id

        hk_val = self.config["hotkeys"].get(action_id, "")
        hk_rec = HotkeyRecorder(hk_val)
        hk_rec.hotkeyChanged.connect(lambda val, k=action_id: self.update_key_config(k, val))
        self.layout.addWidget(hk_rec, self.row_idx, 2)

        joy_val = self.config["joystick"].get(action_id, [])
        joy_rec = JoyRecorder(action_id, "main", joy_val)
        joy_rec.startListening.connect(self.enter_joy_bind_mode)
        joy_rec.cancelled.connect(self.cancel_bind_mode)
        joy_rec.cleared.connect(self.clear_joy_bind)
        
        joy_rec.setProperty("is_hold_row", is_hold)
        
        self.layout.addWidget(joy_rec, self.row_idx, 3)
        self.joy_recorders[action_id] = joy_rec

        self.row_idx += 1

    def update_key_config(self, key, val):
        self.config["hotkeys"][key] = val

    def enter_joy_bind_mode(self, action_id, mode):
        for aid, btn in self.joy_recorders.items():
            if aid != action_id: btn.setChecked(False)
        self.active_action = action_id
        self.input_mgr.binding_mode = True

    def cancel_bind_mode(self):
        self.active_action = None
        self.input_mgr.binding_mode = False

    def clear_joy_bind(self, action_id, mode):
        self.config["joystick"][action_id] = []
        self.joy_recorders[action_id].update_display_text([])

    def on_joy_input(self, dev_name, btn_idx):
        if hasattr(self, 'active_action') and self.active_action:
            btn_widget = self.joy_recorders[self.active_action]
            is_hold_row = btn_widget.property("is_hold_row")
            new_bind = [dev_name, btn_idx, "", 0, is_hold_row]
            
            self.config["joystick"][self.active_action] = new_bind
            btn_widget.update_display_text(new_bind)
            btn_widget.setChecked(False)
            self.cancel_bind_mode()

    def save_test_binds(self):
        for action_id, inp in self.id_inputs.items():
            txt = inp.text().strip()
            if txt:
                self.config["test_ids"][action_id] = int(txt)
            else:
                self.config["test_ids"].pop(action_id, None)

        self.config_handler.save(self.config)
        self.overlay.update_global_hotkeys()
        
        btn = self.sender()
        btn.setText("✔ Saved!")
        QTimer.singleShot(1000, lambda: btn.setText("Save & Apply Test Binds"))

class ClickableTab(QWidget):
    def __init__(self, parent_win, config, bridge):
        super().__init__()
        self.p_win = parent_win
        self.config = config
        self.bridge = bridge
        self.config_handler = parent_win.config_handler

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        left_panel = QWidget(); left_layout = QVBoxLayout(); left_panel.setLayout(left_layout)
        
        self.chk_enable = QCheckBox("Enable Clickable Cockpit")
        self.chk_enable.setStyleSheet("font-weight: bold; font-size: 14px; color: #78aabc;")
        self.chk_enable.toggled.connect(self.toggle_clickable)
        left_layout.addWidget(self.chk_enable)
        
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

        dist_layout = QHBoxLayout()
        dist_layout.addWidget(QLabel("Max Dist (cm):"))
        self.spin_dist = QSpinBox(); self.spin_dist.setRange(1, 500)
        self.spin_dist.setValue(self.config.get("clickable_dist", 60)); self.spin_dist.setSuffix(" cm")
        self.spin_dist.valueChanged.connect(self.save_distance)
        dist_layout.addWidget(self.spin_dist)
        left_layout.addLayout(dist_layout)

        left_layout.addWidget(QLabel("<b>Clickable Points:</b>"))
        self.list_points = QListWidget() 
        self.list_points.setStyleSheet("background: #0f1518; border: 1px solid #444;")
        self.list_points.itemClicked.connect(self.on_point_selected)
        left_layout.addWidget(self.list_points)
        
        self.layout.addWidget(left_panel, 33) 

        right_panel = QGroupBox("POINT EDITOR"); right_layout = QVBoxLayout(); right_panel.setLayout(right_layout)
        
        self.lbl_id = QLabel("ID: -")
        right_layout.addWidget(self.lbl_id)
        right_layout.addWidget(QLabel("Name:"))
        self.edit_name = QLineEdit()
        right_layout.addWidget(self.edit_name)
        right_layout.addWidget(QLabel("Action Type:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(["DCS Command (ID)", "App Function"])
        self.combo_type.currentIndexChanged.connect(self.toggle_input_fields)
        right_layout.addWidget(self.combo_type)
        
        self.group_dcs = QWidget(); l_dcs = QVBoxLayout(); l_dcs.setContentsMargins(0,0,0,0)
        self.group_dcs.setLayout(l_dcs)
        l_dcs.addWidget(QLabel("Command ID (e.g. 3001):"))
        self.spin_cmd_id = QSpinBox(); self.spin_cmd_id.setRange(0, 99999)
        l_dcs.addWidget(self.spin_cmd_id)
        right_layout.addWidget(self.group_dcs)
        
        self.group_app = QWidget(); l_app = QVBoxLayout(); l_app.setContentsMargins(0,0,0,0)
        self.group_app.setLayout(l_app)
        l_app.addWidget(QLabel("Select Function:"))
        self.combo_app_func = QComboBox()
        self.combo_app_func.addItems(sorted(self.config["hotkeys"].keys()))
        l_app.addWidget(self.combo_app_func)
        right_layout.addWidget(self.group_app)
        
        self.btn_save = QPushButton("Update Point")
        self.btn_save.clicked.connect(self.save_point)
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(self.btn_save)

        self.btn_del = QPushButton("Delete Point")
        self.btn_del.clicked.connect(self.delete_point)
        self.btn_del.setStyleSheet("background-color: #c0392b; color: white; margin-top: 5px;")
        right_layout.addWidget(self.btn_del)
        
        right_layout.addStretch()
        self.layout.addWidget(right_panel, 66) 

        self.current_point_data = None
        self.refresh_timer = QTimer(); self.refresh_timer.setInterval(2000); self.refresh_timer.timeout.connect(self.refresh_list)
        self.refresh_timer.start()
        
        self.group_dcs.setVisible(True)
        self.group_app.setVisible(False)
        self.right_panel = right_panel
        self.right_panel.setEnabled(False) 

        self.refresh_list()

    def toggle_clickable(self, checked):
        self.p_win.browser.page().runJavaScript(f"socket.emit('toggle_clickable', {{'state': {str(checked).lower()}}})")

    def update_binding(self, val): self.config["hotkeys"]["mark_click_point"] = val; self.config_handler.save(self.config); self.p_win.overlay.update_global_hotkeys()
    def update_interact_binding(self, val): self.config["hotkeys"]["interact"] = val; self.config_handler.save(self.config); self.p_win.overlay.update_global_hotkeys()
    def save_distance(self, val): self.config["clickable_dist"] = val; self.config_handler.save(self.config)

    def toggle_input_fields(self):
        is_dcs = (self.combo_type.currentIndex() == 0)
        self.group_dcs.setVisible(is_dcs)
        self.group_app.setVisible(not is_dcs)

    def refresh_list(self):
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
        act_type = data.get('action_type', 'dcs')
        idx = 0 if act_type == 'dcs' else 1
        self.combo_type.setCurrentIndex(idx)
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
        if act_type == 'dcs': val = self.spin_cmd_id.value()
        else: val = self.combo_app_func.currentText()
        payload = { "id": self.current_point_data.get('id'), "name": new_name, "action_type": act_type, "action_val": val }
        self.p_win.browser.page().runJavaScript(f"socket.emit('update_clickable_point', {json.dumps(payload)})")
        self.btn_save.setText("Saved!")
        QTimer.singleShot(1000, lambda: self.btn_save.setText("Update Point"))

    def delete_point(self):
        if not self.current_point_data: return
        pid = self.current_point_data.get('id')
        self.p_win.browser.page().runJavaScript(f"socket.emit('delete_clickable_point', {{'id': {pid}}})")
        self.right_panel.setEnabled(False)
        self.edit_name.clear()

# --- MULTIPLAYER TAB ---
class MultiplayerTab(QWidget):
    def __init__(self, parent_win, config):
        super().__init__()
        self.parent_win = parent_win
        self.config = config
        self.setup_ui()
        
        # Timer for polling status
        self.mp_mode = "IDLE"
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_status)
        self.timer.start(2000) # Poll every 2s

    def get_lan_ip(self):
        try:
            # Method 1: Connect to public DNS (Best for finding default route)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            if not ip.startswith('127.'): return ip
        except: pass

        try:
            # Method 2: Connect to common router IP (Heuristic)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(('192.168.1.1', 80))
            ip = s.getsockname()[0]
            s.close()
            if not ip.startswith('127.'): return ip
        except: pass

        try:
            # Method 3: Hostname resolution (can be loopback)
            hostname = socket.gethostname()
            _, _, ip_list = socket.gethostbyname_ex(hostname)
            for ip in ip_list:
                if not ip.startswith('127.') and not ip.startswith('169.254'):
                    return ip
        except: pass
        
        return "127.0.0.1"

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Host Section
        grp_host = QGroupBox("HOST A SESSION")
        host_layout = QGridLayout()
        host_layout.addWidget(QLabel("Port:"), 0, 0)
        self.spin_host_port = QSpinBox(); self.spin_host_port.setRange(1024, 65535)
        self.spin_host_port.setValue(self.config.get("mp_host_port", 5001))
        host_layout.addWidget(self.spin_host_port, 0, 1)
        
        host_layout.addWidget(QLabel("Username:"), 1, 0)
        self.edt_host_user = QLineEdit(self.config.get("mp_host_username", self.config.get("mp_username", "HostAlpha")))
        host_layout.addWidget(self.edt_host_user, 1, 1)
        
        self.btn_host_start = QPushButton("Start Hosting")
        self.btn_host_start.clicked.connect(self.on_host_click)
        self.btn_host_start.setStyleSheet("background-color: #2b4a3b; color: #8fbc8f;")
        host_layout.addWidget(self.btn_host_start, 2, 0, 1, 2)
        
        # UPnP Checkbox
        self.chk_upnp = QCheckBox("Attempt Auto-Forward (UPnP)")
        self.chk_upnp.setChecked(self.config.get("use_upnp", False))
        host_layout.addWidget(self.chk_upnp, 3, 0, 1, 2)

        # -- Persistence Signals (Host) --
        self.spin_host_port.valueChanged.connect(lambda v: self.save_mp_config(host_port=v))
        # -- Persistence Signals (Host) --
        self.spin_host_port.valueChanged.connect(lambda v: self.save_mp_config(host_port=v))
        self.edt_host_user.textChanged.connect(lambda: self.save_mp_config(host_username=self.edt_host_user.text()))
        self.chk_upnp.stateChanged.connect(lambda v: self.save_mp_config(use_upnp=self.chk_upnp.isChecked()))
        self.chk_upnp.stateChanged.connect(lambda v: self.save_mp_config(use_upnp=self.chk_upnp.isChecked()))
        
        # Display Local IP for Sharing
        local_ip = self.get_lan_ip()
        self.lbl_local_ip = QLabel(f"Host IP: {local_ip}")
        self.lbl_local_ip.setStyleSheet("color: #3498db; font-weight: bold; margin-top: 5px;")
        self.lbl_local_ip.setAlignment(Qt.AlignCenter)
        host_layout.addWidget(self.lbl_local_ip, 4, 0, 1, 2)

        # Display Public IP
        self.lbl_public_ip = QLabel("Public IP: ---")
        self.lbl_public_ip.setStyleSheet("color: #8fbc8f; font-weight: bold;")
        self.lbl_public_ip.setAlignment(Qt.AlignCenter)
        host_layout.addWidget(self.lbl_public_ip, 5, 0, 1, 2)

        grp_host.setLayout(host_layout)
        layout.addWidget(grp_host)

        # Client Section
        grp_client = QGroupBox("CONNECT TO HOST")
        client_layout = QGridLayout()
        client_layout.addWidget(QLabel("Host IP:"), 0, 0)
        self.edt_client_ip = QLineEdit(self.config.get("mp_target_ip", "127.0.0.1"))
        client_layout.addWidget(self.edt_client_ip, 0, 1)

        client_layout.addWidget(QLabel("Port:"), 1, 0)
        self.spin_client_port = QSpinBox(); self.spin_client_port.setRange(1024, 65535)
        self.spin_client_port.setValue(self.config.get("mp_target_port", 5001))
        client_layout.addWidget(self.spin_client_port, 1, 1)

        client_layout.addWidget(QLabel("Username:"), 2, 0)
        self.edt_client_user = QLineEdit(self.config.get("mp_client_username", self.config.get("mp_username", "Pilot1")))
        client_layout.addWidget(self.edt_client_user, 2, 1)

        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.on_connect_click)
        self.btn_connect.setStyleSheet("background-color: #2b3a41; color: #78aabc;")
        client_layout.addWidget(self.btn_connect, 3, 0, 1, 2)
        grp_client.setLayout(client_layout)
        layout.addWidget(grp_client)

        # -- Persistence Signals (Client) --
        self.edt_client_ip.textChanged.connect(lambda: self.save_mp_config(target_ip=self.edt_client_ip.text()))
        self.spin_client_port.valueChanged.connect(lambda v: self.save_mp_config(target_port=v))
        self.edt_client_user.textChanged.connect(lambda: self.save_mp_config(client_username=self.edt_client_user.text()))

        # Status
        self.lbl_status = QLabel("STATUS: IDLE")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #777; font-weight: bold; font-size: 14px; border: 1px solid #444; padding: 10px; background: #111;")
        layout.addWidget(self.lbl_status)
        
        self.lbl_connected_clients = QLabel("Connected Pilots:")
        self.lbl_connected_clients.setVisible(False)
        layout.addWidget(self.lbl_connected_clients)
        
        self.list_users = QListWidget()
        self.list_users.setStyleSheet("background: #0f1518; border: 1px solid #444; max-height: 100px;")
        self.list_users.setVisible(False)
        layout.addWidget(self.list_users)

        self.list_users.setVisible(False)
        layout.addWidget(self.list_users)

        self.list_users = QListWidget()
        self.list_users.setStyleSheet("background: #0f1518; border: 1px solid #444; max-height: 100px;")
        self.list_users.setVisible(False)
        layout.addWidget(self.list_users)

        layout.addStretch()
        
        # --- QUIT APP BUTTON ---
        self.btn_quit = QPushButton("QUIT APPLICATION")
        self.btn_quit.clicked.connect(self.stop_application)
        self.btn_quit.setStyleSheet("background-color: #5a1a1a; color: #ffcccc; font-weight: bold; border: 1px solid #ff0000; margin-top:20px;")
        layout.addWidget(self.btn_quit)
        
        self.setLayout(layout)

    def on_host_click(self):
        if self.mp_mode == "HOST": self.stop_mp()
        else: self.start_host()

    def on_connect_click(self):
        if self.mp_mode == "CLIENT": self.stop_mp()
        else: self.connect_client()

    def start_host(self):
        port = self.spin_host_port.value()
        user = self.edt_host_user.text()
        use_upnp = self.chk_upnp.isChecked()
        
        self.save_mp_config(host_port=port, host_username=user, use_upnp=use_upnp)
        
        payload = {"port": port, "username": user, "use_upnp": use_upnp}
        try:
            requests.post(f"{SERVER_URL}/api/mp/host/start", json=payload, timeout=2)
            self.poll_status()
        except: pass

    def connect_client(self):
        ip = self.edt_client_ip.text()
        port = self.spin_client_port.value()
        user = self.edt_client_user.text()
        self.save_mp_config(target_ip=ip, target_port=port, client_username=user)
        
        payload = {
            "ip": ip, 
            "port": port, 
            "username": user
        }
        try:
            requests.post(f"{SERVER_URL}/api/mp/client/connect", json=payload, timeout=2)
            self.poll_status()
        except: pass
        
    def save_mp_config(self, host_port=None, target_ip=None, target_port=None, host_username=None, client_username=None, use_upnp=None):
        if host_port: self.config["mp_host_port"] = host_port
        if target_ip: self.config["mp_target_ip"] = target_ip
        if target_port: self.config["mp_target_port"] = target_port
        if host_username: self.config["mp_host_username"] = host_username
        if client_username: self.config["mp_client_username"] = client_username
        if use_upnp is not None: self.config["use_upnp"] = use_upnp
        self.parent_win.config_handler.save(self.config)

    def stop_mp(self):
        try: requests.post(f"{SERVER_URL}/api/mp/stop", timeout=2)
        except: pass
        self.poll_status()

    def stop_application(self):
        reply = QMessageBox.question(self, 'Exit', 'Shutdown Request: Make sure you saved your mission.\nExit Application?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try: requests.post(f"{SERVER_URL}/api/app/shutdown", timeout=1)
            except: pass
            sys.exit(0)

    def poll_status(self):
        try:
            r = requests.get(f"{SERVER_URL}/api/mp/status", timeout=1)
            if r.status_code == 200:
                data = r.json()
                mode = data.get("mode", "IDLE")
                users = data.get("users", 0)
                self.mp_mode = mode # Update local state
                
                if mode == "HOST":
                    self.lbl_status.setText(f"HOSTING ({users} Clients)")
                    self.lbl_status.setStyleSheet("color: #00ff00; border: 1px solid #00ff00; background: #0a200a; font-weight: bold; padding: 10px;")
                    
                    # Update Public IP and UPnP Status
                    pub_ip = data.get("public_ip")
                    upnp_stat = data.get("upnp_status", "Disabled")
                    
                    if pub_ip:
                        self.lbl_public_ip.setText(f"Public IP: {pub_ip}")
                        if upnp_stat == "Active":
                            self.lbl_public_ip.setToolTip("UPnP Forwarding Active (Port Open)")
                            self.lbl_public_ip.setStyleSheet("color: #00ff00; font-weight: bold;")
                        else:
                            self.lbl_public_ip.setToolTip("Public IP Detected (Manual Port Forwarding May Be Required)")
                            self.lbl_public_ip.setStyleSheet("color: #f1c40f; font-weight: bold;")
                    else:
                        self.lbl_public_ip.setText("Public IP: ---")
                        self.lbl_public_ip.setStyleSheet("color: #8fbc8f; font-weight: bold;")
                    
                    self.btn_host_start.setText("Stop Hosting")
                    self.btn_host_start.setStyleSheet("background-color: #5a2b2b; color: #e74c3c;")
                    self.btn_host_start.setEnabled(True)
                    self.btn_connect.setEnabled(False)
                    self.btn_connect.setText("Connect")
                    self.btn_connect.setStyleSheet("background-color: #2b3a41; color: #78aabc;")
                    
                    self.update_client_list(data.get("clients", []))
                elif mode == "CLIENT":
                    self.lbl_status.setText(f"CONNECTED to {data.get('ip')}")
                    self.lbl_status.setStyleSheet("color: #00ffff; border: 1px solid #00ffff; background: #0a2020; font-weight: bold; padding: 10px;")
                    
                    self.btn_connect.setText("Disconnect")
                    self.btn_connect.setStyleSheet("background-color: #5a2b2b; color: #e74c3c;")
                    self.btn_connect.setEnabled(True)
                    self.btn_host_start.setEnabled(False)
                    self.btn_host_start.setText("Start Hosting")
                    self.btn_host_start.setStyleSheet("background-color: #2b4a3b; color: #8fbc8f;")
                    
                    self.hide_client_list()
                else:
                    self.lbl_status.setText("STATUS: IDLE")
                    self.lbl_status.setStyleSheet("color: #777; border: 1px solid #444; background: #111; font-weight: bold; padding: 10px;")
                    
                    # Reset Public IP Label
                    self.lbl_public_ip.setText("Public IP: ---")
                    self.lbl_public_ip.setStyleSheet("color: #8fbc8f; font-weight: bold;")
                    self.lbl_public_ip.setToolTip("")
                    
                    self.btn_host_start.setText("Start Hosting")
                    self.btn_host_start.setStyleSheet("background-color: #2b4a3b; color: #8fbc8f;")
                    self.btn_host_start.setEnabled(True)
                    
                    self.btn_connect.setText("Connect")
                    self.btn_connect.setStyleSheet("background-color: #2b3a41; color: #78aabc;")
                    self.btn_connect.setEnabled(True)
                    
                    self.hide_client_list()
        except: 
            self.lbl_status.setText("OFFLINE")
            self.lbl_status.setStyleSheet("color: #RED;")
            
    def update_client_list(self, clients):
        self.lbl_connected_clients.setVisible(True)
        self.list_users.setVisible(True)
        self.list_users.clear()
        for c in clients:
            self.list_users.addItem(c)
            
    def hide_client_list(self):
        self.lbl_connected_clients.setVisible(False)
        self.list_users.setVisible(False)

class SettingsWindow(QWidget):
    def __init__(self, overlay_ref, config, config_handler, input_mgr):
        super().__init__()
        self.overlay = overlay_ref
        self.browser = overlay_ref.browser
        self.config = config
        self.config_handler = config_handler
        self.input_mgr = input_mgr
        self.loading = True
        
        self.geo_timer = QTimer()
        self.geo_timer.setSingleShot(True)
        self.geo_timer.setInterval(200)
        self.geo_timer.timeout.connect(self.push_settings)

        self.setWindowTitle("Settings")
        self.setGeometry(100, 100, 550, 750)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setStyleSheet(STYLES)
        
        self.tabs = QTabWidget()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.tabs)

        self.tab_multiplayer = MultiplayerTab(self, self.config)
        self.tabs.addTab(self.tab_multiplayer, "Connection")

        self.tab_hud = HUDTab(self)
        self.tabs.addTab(self.tab_hud, "HUD Display")

        self.tab_controls = ControlsTab(self, self.config, self.input_mgr)
        self.tabs.addTab(self.tab_controls, "Controls")

        self.tab_pointer = PointerTab(self, self.config, self.input_mgr)
        self.tabs.addTab(self.tab_pointer, "Virtual Pointer")

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
                self.prof_combo.clear()
                self.prof_combo.addItems(data.get("profiles_list", ["Default"]))
                self.prof_combo.setCurrentText(data.get("current_profile", "Default"))
                self.apply_ui_settings(data.get("settings", {}))
                clickable_state = data.get("clickable_enabled", False)
                if hasattr(self, 'tab_clickable'):
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
    force_hud = pyqtSignal(bool)
    force_settings = pyqtSignal(bool)
    trigger_test_single = pyqtSignal(str)      
    trigger_test_hold = pyqtSignal(str, bool)
    toggle_pointer_mode = pyqtSignal()

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
        elif action_name == "pointer_toggle": self.toggle_pointer_mode.emit()
        elif action_name.startswith("test_single_"): self.handle_test_single(action_name)


    def switch_change(self, action_name, state):
        if action_name == "toggle_hud": self.force_hud.emit(state)
        elif action_name == "settings": self.force_settings.emit(state)
        elif action_name.startswith("test_hold_"): self.handle_test_hold(action_name, state)
        elif state: self.button_press(action_name)
    def handle_test_single(self, action_name):
        self.trigger_test_single.emit(action_name)

    def handle_test_hold(self, action_name, state):
        self.trigger_test_hold.emit(action_name, state)    

    # --- POINTER METHODS ---
    def send_pointer_motion(self, d1, d2, mode):
        # Throttle? For now direct relay.
        # d1, d2 = dx, dy (if relative) or x, y (if abs)
        payload = {'dx': d1, 'dy': d2, 'mode': 'rel'} # Default to rel for now
        if mode.startswith('axis') or mode == 'mouse_rel':
             payload = {'dx': d1, 'dy': d2, 'mode': 'rel'}
        elif mode == 'abs' or mode == 'mouse_abs':
             payload = {'x': d1, 'y': d2, 'mode': 'abs'}
        elif mode == 'mouse_pct':
             payload = {'x': d1, 'y': d2, 'mode': 'pct'}
        
        # We need access to browser to emit. 
        # HotkeyBridge doesn't store browser ref directly, it's connected to signals usually.
        # But here we need to emit socket event.
        # We can emit a PyQt Signal that HUDOverlay listens to, OR we can inject the browser ref.
        self.trigger_pointer_socket.emit('virtual_pointer_update', payload)

    def send_pointer_button(self, action, state):
        # action: "click"
        # state: True (Down), False (Up)
        evt = 'down' if state else 'up'
        self.trigger_pointer_socket.emit('virtual_click', {'action': evt})

    trigger_pointer_socket = pyqtSignal(str, dict) # event, data    

# --- MAIN APP ---
class HUDOverlay(QMainWindow):
    def __init__(self, config_manager, bridge_ref, input_mgr):
        super().__init__()
        self.config_handler = config_manager
        self.config = self.config_handler.load() # Load initial config
        self.bridge = bridge_ref
        self.input_mgr = input_mgr
        
        self.pointer_active = False # Local State
        
        # Connect Input Manager Signals
        self.input_mgr.pointer_motion.connect(self.bridge.send_pointer_motion)
        self.input_mgr.pointer_button.connect(self.bridge.send_pointer_button)
        self.bridge.trigger_pointer_socket.connect(self.emit_socket_event)
        
        # Pointer Toggle Logic
        # We intercept the 'pointer_toggle' button press in HotkeyBridge via button_press?
        # HotkeyBridge emits specific signals. We should add one for pointer toggle.
        self.bridge.toggle_pointer_mode.connect(self.toggle_pointer)


        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput); self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_NoSystemBackground)
        self.browser = QWebEngineView(); self.browser.setAttribute(Qt.WA_TranslucentBackground); self.browser.setStyleSheet("background: transparent;"); self.browser.page().setBackgroundColor(Qt.transparent); self.browser.setUrl(QUrl(HUD_URL)); self.setCentralWidget(self.browser)
        
        self.settings_window = SettingsWindow(self, self.config, self.config_handler, self.input_mgr)
        self.testing_window = TestingWindow(self, self.config, self.input_mgr)
        
        # CONNECTIONS
        self.input_mgr.button_pulse.connect(self.bridge.button_press)
        self.input_mgr.switch_change.connect(self.bridge.switch_change)

    def toggle_overlay(self): (self.hide() if self.isVisible() else self.show())
    def toggle_settings(self): (self.settings_window.hide() if self.settings_window.isVisible() else (self.settings_window.show(), self.settings_window.activateWindow()))
    def toggle_testing(self): (self.testing_window.hide() if self.testing_window.isVisible() else (self.testing_window.show(), self.testing_window.activateWindow()))

    def set_overlay_visible(self, visible): (self.show() if visible else self.hide())

    def emit_socket_event(self, event, data):
        # Intercept Absolute Mouse movement to make it Monitor-Relative %
        if event == 'virtual_pointer_update' and data.get('mode') == 'abs':
            # Transform Global Coordinates -> Percentage of Current Monitor
            global_x = data.get('x', 0)
            global_y = data.get('y', 0)
            
            # Find which screen the mouse is on
            screens = QApplication.screens()
            target_screen = None
            for s in screens:
                if s.geometry().contains(int(global_x), int(global_y)):
                    target_screen = s
                    break
            
            if target_screen:
                rect = target_screen.geometry()
                pct_x = (global_x - rect.x()) / rect.width()
                pct_y = (global_y - rect.y()) / rect.height()
                
                # Clamp
                pct_x = max(0.0, min(1.0, pct_x))
                pct_y = max(0.0, min(1.0, pct_y))
                
                data['x'] = pct_x
                data['y'] = pct_y
                data['mode'] = 'pct'
            else:
                # Fallback to window relative if screen not found? Or just 0.5
                 data['x'] = 0.5
                 data['y'] = 0.5
                 data['mode'] = 'pct'

        # Always emit pointer-related events (server manages active state)
        safe_emit = f"if (typeof socket !== 'undefined') socket.emit('{event}', {json.dumps(data)})"
        if 'pointer' in event or event in ['toggle_pointer_mode', 'virtual_pointer_update', 'virtual_click']:
            self.browser.page().runJavaScript(safe_emit)
        elif self.pointer_active:
            self.browser.page().runJavaScript(safe_emit)

    def toggle_pointer(self):
        self.pointer_active = not self.pointer_active
        # Reset mouse relative tracking when activating
        if self.pointer_active:
            self.input_mgr.reset_mouse_state()
            
        self.emit_socket_event('toggle_pointer_mode', {'active': self.pointer_active})
    def set_settings_visible(self, visible):
        if visible: 
            self.settings_win.show()
            self.settings_win.activateWindow()
        else: 
            self.settings_win.hide()

    def stop_application(self):
        return self.settings_win.tab_multiplayer.stop_application()

    def update_global_hotkeys(self):
        InputBinder.clear_all()
        hk = self.config["hotkeys"]

        def bind(name, signal):
            key = hk.get(name)
            if key and isinstance(key, str) and key.strip():
                InputBinder.bind(key, signal.emit)

        try:
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
            bind("pointer_toggle", self.bridge.toggle_pointer_mode)  # ADDED: Pointer toggle keybind
            
            # Pointer click for keyboard/mouse buttons - needs DOWN and UP events
            pointer_click_key = hk.get("pointer_click")
            if pointer_click_key and isinstance(pointer_click_key, str) and pointer_click_key.strip():
                # 1. Try Mouse Button State
                if InputBinder.bind_mouse_button_state(
                    pointer_click_key,
                    lambda: self.bridge.send_pointer_button("click", True),   # DOWN
                    lambda: self.bridge.send_pointer_button("click", False)   # UP
                ):
                    pass
                
                # 2. Try Keyboard Key State
                elif InputBinder.bind_keyboard_state(
                    pointer_click_key,
                    lambda: self.bridge.send_pointer_button("click", True),   # DOWN
                    lambda: self.bridge.send_pointer_button("click", False)   # UP
                ):
                    pass                  
                
                # 3. Fallback (Complex Hotkeys or errors) - Simulate Click
                else:
                    InputBinder.bind(pointer_click_key, lambda: (
                        self.bridge.send_pointer_button("click", True),
                        QTimer.singleShot(50, lambda: self.bridge.send_pointer_button("click", False))
                    ))

            for action_name, key_val in hk.items():
                if not key_val or not isinstance(key_val, str) or not key_val.strip(): continue

                if action_name.startswith("test_single_"):
                    InputBinder.bind(key_val, lambda n=action_name: self.bridge.trigger_test_single.emit(n))
                
                elif action_name.startswith("test_hold_"):
                    # We can't strictly use InputBinder for complex hold logic with 'keyboard' lib via static method simply
                    # But we can try to access the library directly or assume InputBinder supports press/release if we extended it.
                    # For now, we revert to direct keyboard usage for HOLDs as in original ID Hunter
                    try:
                        import keyboard # Import here if needed, or rely on global
                        keyboard.on_press_key(key_val, lambda e, n=action_name: self.bridge.trigger_test_hold.emit(n, True))
                        keyboard.on_release_key(key_val, lambda e, n=action_name: self.bridge.trigger_test_hold.emit(n, False))
                    except: pass
            
        except Exception as e: 
            print(f"Bind Error: {e}")

def run():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Keep running for System Tray
    
    # Init Config Manager
    config_mgr = OverlayConfig(CONFIG_FILE)
    config = config_mgr.load() # Initial load
    
    # Init Bridge (Signals)
    bridge = HotkeyBridge()

    def execute_test_single(action_name):
        cmd_id = config.get("test_ids", {}).get(action_name)
        if cmd_id:
            overlay.browser.page().runJavaScript(f"socket.emit('dcs_cmd', {{'id': {cmd_id}, 'val': 1, 'duration': 0.1}})")

    def execute_test_hold(action_name, state):
        cmd_id = config.get("test_ids", {}).get(action_name)
        if cmd_id:
            if state: overlay.browser.page().runJavaScript(f"socket.emit('dcs_loop_start', {{'id': {cmd_id}}})")
            else: overlay.browser.page().runJavaScript(f"socket.emit('dcs_loop_stop', {{'id': {cmd_id}}})")

    bridge.trigger_test_single.connect(execute_test_single)
    bridge.trigger_test_hold.connect(execute_test_hold)
    
    # Init Input Manager (Joystick/Hardware)
    input_mgr = InputManager(config)
    
    # Capture Screen Geometry for Absolute Mouse Mode
    def update_screens():
        screens = []
        for s in app.screens():
            g = s.geometry()
            screens.append({'x': g.x(), 'y': g.y(), 'w': g.width(), 'h': g.height()})
        input_mgr.set_screen_geometry(screens)
    
    update_screens() # Initial capture
    
    input_mgr.start()
    
    # Init Overlay
    overlay = HUDOverlay(config_mgr, bridge, input_mgr)
    overlay.show() 
    
    # Connect Logic
    bridge.toggle_hud.connect(overlay.toggle_overlay)
    bridge.toggle_settings.connect(overlay.toggle_settings)
    bridge.toggle_testing.connect(overlay.toggle_testing)
    bridge.force_hud.connect(overlay.set_overlay_visible)
    bridge.force_settings.connect(overlay.set_settings_visible)

    # DCS & Server Commands
    bridge.trigger_trim_left.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('dcs_cmd', {'id': 197, 'val': 1, 'duration': 0.2})"))
    bridge.trigger_mark.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('mark_look_point')"))
    bridge.trigger_debug.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('debug_dummy_marker')"))
    bridge.trigger_set_active_poi.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('activate_last_poi')"))
    bridge.trigger_cycle_next.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('cycle_wp', {'dir': 1})"))
    bridge.trigger_cycle_prev.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('cycle_wp', {'dir': -1})"))
    bridge.trigger_restore_route.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('restore_last_route')"))
    bridge.toggleAP.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('toggleAP')"))
    bridge.trigger_mark_click.connect(lambda: overlay.browser.page().runJavaScript( f"socket.emit('mark_clickable_point', {{'dist': {config.get('clickable_dist', 60)}}})" ))
    bridge.trigger_interact.connect(lambda: overlay.browser.page().runJavaScript("socket.emit('interact_at_mouse')"))

    # Initial Hotkey Bind
    overlay.update_global_hotkeys()
    
    # Open Settings on Boot
    overlay.toggle_settings()
    
    # --- SYSTEM TRAY ---
    # Find Icon
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        # Check for _internal folder (PyInstaller 5.x+ onedir default)
        internal = os.path.join(base_path, "_internal")
        if os.path.exists(internal):
            base_path = internal
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Go up from modules/
        
    icon_path = os.path.join(base_path, "static", "icons", "favicon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(base_path, "DATA", "icon.ico") # Fallback?
    
    tray_icon = QSystemTrayIcon(QIcon(icon_path), app)
    tray_icon.setToolTip("DCS Route Manager")
    
    tray_menu = QMenu()
    
    a_show = QAction("Show Overlay / Settings", tray_menu)
    a_show.triggered.connect(overlay.toggle_settings)
    tray_menu.addAction(a_show)
    
    a_map = QAction("Open Web Map", tray_menu)
    a_map.triggered.connect(lambda: webbrowser.open(f"{SERVER_URL}"))
    tray_menu.addAction(a_map)
    
    tray_menu.addSeparator()
    
    a_exit = QAction("Exit Application", tray_menu)
    a_exit.triggered.connect(overlay.stop_application)
    tray_menu.addAction(a_exit)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()