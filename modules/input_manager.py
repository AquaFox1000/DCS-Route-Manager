import os
import json
import time
import keyboard
import mouse
import threading

# Pygame for Joystick Support
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

from PyQt5.QtCore import QObject, QThread, pyqtSignal

# --- CONFIGURATION MANAGER ---
class OverlayConfig:
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
        },
        "test_ids": {}
    }

    def __init__(self, config_file):
        self.config_file = config_file

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    config = self.DEFAULT_CONFIG.copy()
                    config["hotkeys"].update(data.get("hotkeys", {}))
                    config.setdefault("joystick", {})
                    config["joystick"].update(data.get("joystick", {}))
                    config.setdefault("test_ids", {})
                    config["test_ids"].update(data.get("test_ids", {}))
                    return config
            except Exception as e:
                print(f"Error loading config: {e}")
        return self.DEFAULT_CONFIG.copy()

    def save(self, config):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")


# --- GLOBAL INPUT BINDER (Static Helper) ---
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
            def safe_trigger():
                try: callback()
                except: pass

            try:
                hook = mouse.on_button(safe_trigger, buttons=mouse_map[trigger], types=mouse.UP)
                InputBinder._mouse_hooks.append(hook)
            except ImportError:
                print("Mouse library error or missing.")
            return

        # 2. Handle Scroll Binds
        if trigger in ['scroll_up', 'scroll_down']:
            def scroll_handler(e):
                if isinstance(e, mouse.WheelEvent):
                    if trigger == 'scroll_up' and e.delta > 0: callback()
                    elif trigger == 'scroll_down' and e.delta < 0: callback()
            
            try:
                InputBinder._mouse_hooks.append(mouse.hook(scroll_handler))
            except Exception: pass
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


# --- JOYSTICK WORKER (Background Thread) ---
class InputManager(QThread):
    # Unified Signals
    button_pulse = pyqtSignal(str)          # For momentary actions
    switch_change = pyqtSignal(str, bool)   # For stateful toggles
    
    # Binding Support Signals
    bind_detected = pyqtSignal(str, int)    # Emits (DeviceName, ButtonIndex)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        self.binding_mode = False 
        self.joysticks = {}
        self._init_pygame()

    @staticmethod
    def get_cursor_position():
        """ 
        Returns global (x, y) cursor position. 
        Safe for use in server.py (Passive Import).
        """
        try:
            return mouse.get_position()
        except:
            return None

    def _init_pygame(self):
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
