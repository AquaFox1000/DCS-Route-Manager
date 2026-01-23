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
        "axes": {
            # Format: "action_id": [DevName, AxisIdx, Invert(bool), Scale(float)]
        },
        "digital_sensitivity": 1.0, 
        "mouse_sensitivity": 1.0,
        "mouse_enabled": False,
        "mouse_mode": "rel",
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
                    
                    # Update all top-level keys (scalars and dicts)
                    for k, v in data.items():
                        if k in config and not isinstance(config[k], dict):
                            config[k] = v
                    
                    # Specific merge for nested dicts to preserve structure
                    config["hotkeys"].update(data.get("hotkeys", {}))
                    config.setdefault("joystick", {})
                    config["joystick"].update(data.get("joystick", {}))
                    config.setdefault("axes", {})
                    config["axes"].update(data.get("axes", {}))
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
    _pressed_keys = set()
    
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
    def bind_mouse_button_state(trigger_str, down_callback, up_callback):
        """ Binds a mouse button to separate down and up callbacks """
        if not trigger_str: return
        
        trigger = trigger_str.lower().strip()
        mouse_map = {
            'left_click': 'left', 'right_click': 'right', 'middle_click': 'middle',
            'mouse_back': 'x', 'mouse_fwd': 'x2'
        }
        
        if trigger in mouse_map:
            try:
                # Hook for button down
                def on_down():
                    try: down_callback()
                    except: pass
                    
                # Hook for button up  
                def on_up():
                    try: up_callback()
                    except: pass
                
                hook_down = mouse.on_button(on_down, buttons=mouse_map[trigger], types=mouse.DOWN)
                hook_up = mouse.on_button(on_up, buttons=mouse_map[trigger], types=mouse.UP)
                InputBinder._mouse_hooks.append(hook_down)
                InputBinder._mouse_hooks.append(hook_up)
                print(f"✅ Bound mouse button {trigger} to down/up callbacks")
            except Exception as e:
                print(f"Mouse binding error: {e}")
            return True
        return False


    def bind_keyboard_state(trigger_str, down_callback, up_callback):
        """ Binds a keyboard key to separate down and up callbacks """
        if not trigger_str: return
        
        trigger = trigger_str.lower().strip()
        
        # Check if it's a mouse bind first (ignore here)
        mouse_map = {
            'left_click': 'left', 'right_click': 'right', 'middle_click': 'middle',
            'mouse_back': 'x', 'mouse_fwd': 'x2'
        }
        if trigger in mouse_map: return False

        try:
            # We need to wrap callbacks to accept the event argument that keyboard passes
            # And prevent repeats!
            def on_down(e): 
                if e.name in InputBinder._pressed_keys: return
                InputBinder._pressed_keys.add(e.name)
                try: down_callback()
                except: pass
            
            def on_up(e):
                if e.name in InputBinder._pressed_keys:
                    InputBinder._pressed_keys.remove(e.name)
                try: up_callback()
                except: pass

            hk_down = keyboard.on_press_key(trigger, on_down)
            hk_up = keyboard.on_release_key(trigger, on_up)
            
            return True
        except Exception as e:
            print(f"Keyboard state bind error (maybe complex hotkey?): {e}")
            return False

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
        InputBinder._pressed_keys.clear()


# --- JOYSTICK WORKER (Background Thread) ---
class InputManager(QThread):
    # Unified Signals
    button_pulse = pyqtSignal(str)          # For momentary actions
    switch_change = pyqtSignal(str, bool)   # For stateful toggles
    
    # Pointer Signals [NEW]
    pointer_motion = pyqtSignal(float, float, str) # val1, val2, mode ("rel" or "abs")
    pointer_button = pyqtSignal(str, bool)         # action, is_pressed
    
    # Binding Support Signals
    bind_detected = pyqtSignal(str, int)    # Emits (DeviceName, ButtonIndex)
    axis_detected = pyqtSignal(str, int)    # Emits (DeviceName, AxisIndex)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        self.binding_mode = False 
        self.joysticks = {}
        self.mouse_hook_ref = None
        self.last_mouse_pos = None
        self.digital_state = {"up": False, "down": False, "left": False, "right": False}
        self.axis_state = {"x": 0.0, "y": 0.0}  # Accumulated axis values
        self.monitor_rects = [] # List of screen geometries
        self._init_pygame()

    def enable_mouse_hook(self, enable=True):
        if enable and not self.mouse_hook_ref:
            try:
                self.last_mouse_pos = mouse.get_position()
                self.mouse_hook_ref = mouse.hook(self._mouse_callback)
                print("🖱️ Mouse Hook ENABLED")
            except Exception as e:
                print(f"Mouse Hook Error: {e}")
        elif not enable and self.mouse_hook_ref:
            try:
                mouse.unhook(self.mouse_hook_ref)
                self.mouse_hook_ref = None
                print("🖱️ Mouse Hook DISABLED")
            except: pass

    def reset_mouse_state(self):
        """ Resets the last tracking position to current mouse pos """
        try:
            self.last_mouse_pos = mouse.get_position()
        except: pass

    def set_screen_geometry(self, screens):
        """ 
        Update known screen rectangles.
        screens: List of dicts {'x': int, 'y': int, 'w': int, 'h': int}
        """
        self.monitor_rects = screens
        print(f"🖥️ InputManager: Updated Screen Geometry: {self.monitor_rects}")

    def _mouse_callback(self, event):
        # Runs in background thread
        if isinstance(event, mouse.MoveEvent):
            curr_x, curr_y = event.x, event.y
            
            # Check config for mode (default to relative if not specified but hook is active)
            # We assume hook is only active if enabled in config
            mode = self.config.get("mouse_mode", "rel")
            
            if mode == "abs":
                 # Determine which monitor we are on
                 found_rect = None
                 for rect in self.monitor_rects:
                     if (curr_x >= rect['x'] and curr_x < rect['x'] + rect['w'] and
                         curr_y >= rect['y'] and curr_y < rect['y'] + rect['h']):
                         found_rect = rect
                         break
                 
                 if found_rect:
                     # Normalize 0.0 - 1.0 relative to that monitor
                     pct_x = (curr_x - found_rect['x']) / found_rect['w']
                     pct_y = (curr_y - found_rect['y']) / found_rect['h']
                     # Clamp
                     pct_x = max(0.0, min(1.0, pct_x))
                     pct_y = max(0.0, min(1.0, pct_y))
                     self.pointer_motion.emit(float(pct_x), float(pct_y), "mouse_pct")
                 else:
                     # Fallback to raw or just don't emit if outside known bounds
                     # Keep raw just in case
                     self.pointer_motion.emit(float(curr_x), float(curr_y), "mouse_abs")

            else:
                # relative
                if self.last_mouse_pos:
                    dx = curr_x - self.last_mouse_pos[0]
                    dy = curr_y - self.last_mouse_pos[1]
                    if dx != 0 or dy != 0:
                        mouse_sens = self.config.get("mouse_sensitivity", 1.0)
                        self.pointer_motion.emit(float(dx * mouse_sens), float(dy * mouse_sens), "mouse_rel")
                    
            self.last_mouse_pos = (curr_x, curr_y)

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
            # Set dummy driver for headless/embedded operation to avoid video system errors
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.init()
            pygame.display.init() # Ensure display is init even with dummy driver
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
                    
                    # --- BINDING MODE ---
                    if self.binding_mode:
                        if event.type == pygame.JOYBUTTONDOWN:
                            joy_obj = self.joysticks.get(event.instance_id)
                            if joy_obj:
                                self.bind_detected.emit(joy_obj.get_name(), event.button)
                                time.sleep(0.3)
                        elif event.type == pygame.JOYAXISMOTION:
                            if abs(event.value) > 0.5: # Threshold
                                joy_obj = self.joysticks.get(event.instance_id)
                                if joy_obj:
                                    self.axis_detected.emit(joy_obj.get_name(), event.axis)
                                    time.sleep(0.3)
                        continue

                    # --- NORMAL MODE ---
                    if event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
                        joy_obj = self.joysticks.get(event.instance_id)
                        if not joy_obj: continue
                        self.check_binds(joy_obj.get_name(), event.button, event.type == pygame.JOYBUTTONDOWN)
                    
                    elif event.type == pygame.JOYAXISMOTION:
                        joy_obj = self.joysticks.get(event.instance_id)
                        if not joy_obj: continue
                        self.check_axes(joy_obj.get_name(), event.axis, event.value)
                
                # --- DIGITAL LOOP (Continuous Movement) ---
                dx, dy = 0.0, 0.0
                # Base speed adjusted by sensitivity
                base_speed = 5.0
                dig_sens = self.config.get("digital_sensitivity", 1.0)
                speed = base_speed * dig_sens
                
                hk_cfg = self.config.get("hotkeys", {})
                def is_k(name):
                    k = hk_cfg.get(name)
                    return k and keyboard.is_pressed(k)

                if is_k("pointer_left") or self.digital_state["left"]: dx -= speed
                if is_k("pointer_right") or self.digital_state["right"]: dx += speed
                if is_k("pointer_up") or self.digital_state["up"]: dy -= speed
                if is_k("pointer_down") or self.digital_state["down"]: dy += speed
                
                if dx != 0 or dy != 0:
                    self.pointer_motion.emit(dx, dy, "digital_rel")
                
                # --- ANALOG LOOP (Emit accumulated axis values) ---
                ax = self.axis_state["x"] * 20.0  # Convert -1..1 range to pixels/tick
                ay = self.axis_state["y"] * 20.0
                
                if abs(ax) > 0.1 or abs(ay) > 0.1:  # Emit if above threshold
                    self.pointer_motion.emit(ax, ay, "axis_rel")

                time.sleep(0.01) # 100Hz poll
            except Exception as e:
                print(f"Joy Loop Error: {e}")
                time.sleep(1)

    def check_axes(self, dev_name, axis_idx, value):
        axes_cfg = self.config.get("axes", {})
        DEADZONE = 0.05
        if abs(value) < DEADZONE: value = 0.0
        
        for action, bind in axes_cfg.items():
            if not bind or len(bind) < 2: continue
            
            # Format: [DevName, AxisIdx, Invert, Scale]
            if bind[0] in dev_name and bind[1] == axis_idx:
                scale = bind[3] if len(bind) > 3 else 1.0
                invert = bind[2] if len(bind) > 2 else False
                final = value * scale * (-1 if invert else 1)
                
                # Store in axis state (don't emit yet, accumulate)
                if action == "pointer_x":
                    self.axis_state["x"] = final
                elif action == "pointer_y":
                    self.axis_state["y"] = final

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

                # POINTER ACTIONS
                if action_name.startswith("pointer_"):
                    if action_name == "pointer_click":
                        print(f"🖱️ Click button: {'DOWN' if is_pressed else 'UP'}")
                        self.pointer_button.emit("click", is_pressed)
                    elif action_name == "pointer_left":  self.digital_state["left"] = is_pressed
                    elif action_name == "pointer_right": self.digital_state["right"] = is_pressed
                    elif action_name == "pointer_up":    self.digital_state["up"] = is_pressed
                    elif action_name == "pointer_down":  self.digital_state["down"] = is_pressed
                    elif action_name == "pointer_toggle":
                         if is_pressed: self.button_pulse.emit(action_name)
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
