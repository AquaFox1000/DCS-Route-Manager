# server.py 
from gevent import monkey
monkey.patch_all()

# --- 1. IMPORTS (STDLIB -> 3RD PARTY -> LOCAL) ---
import socket
import json
import math
import threading
import os
import sys
import time
import keyboard 
import subprocess
import atexit

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO

# Local Modules
from modules.nav_computer import NavComputer
from modules.utils import MathUtils
from modules.input_manager import InputManager
from modules.tcp_connector import DCSHookClient

# --- 2. CONFIGURATION ---
UDP_IP = "127.0.0.1"
UDP_PORT = 11000
DCS_INPUT_ADDR = ("127.0.0.1", 11001)
WEB_PORT = 5000
SERVER_BOOT_ID = time.time()
CLICK_HIT_RADIUS = 13
TCP_PORT = 11002

DATA_DIR = "DATA"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ROUTES_FILE = os.path.join(DATA_DIR, "saved_routes.json")
HUD_CONFIG_FILE = os.path.join(DATA_DIR, "hud_config.json")
MAP_CONFIG_FILE = os.path.join(DATA_DIR, "map_config.json")
POIS_FILE = os.path.join(DATA_DIR, "saved_pois.json")
CLICKABLE_FILE = os.path.join(DATA_DIR, "clickable_point_data.json")

# --- DCS COMMAND MAPPING ---
AP_KEY_MAP = {
    "PITCH_UP":   (195, 196), 
    "PITCH_DOWN": (193, 194), 
    "ROLL_LEFT":  (197, 198), 
    "ROLL_RIGHT": (199, 200)  
}

# --- 3. GLOBAL VARIABLES ---
last_known_telemetry = {}
captured_look_data = None
valid_look_cache = {"lat": 0, "lon": 0, "alt": 0, "time": 0}
tgt_sequence_id = 1
last_standard_route_cache = {"route": [], "index": -1}
active_route_name = None
active_command_loops = set()
clickable_mode_enabled = False
last_pitch_time = 0
ap_axis_locks = { "pitch": False, "roll": False }
phonebook = {}  # Unit ID → Player Name mapping (from DCS Hook)
last_metadata = None # Cache for player context

# --- 4. FLASK & MODULE INITIALIZATION ---
app = Flask(__name__, static_folder='state')
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='gevent')

# Initialize Modules
nav = NavComputer()

# Custom callback for TCP messages
def handle_tcp_message(event_name, data):
    """Intercepts TCP messages from DCS Hook before emitting to web clients"""
    global phonebook
    global last_metadata
    
    if event_name == 'phonebook':
        # Update server-side phonebook state
        phonebook = data
        print(f"📞 Phonebook updated: {len(data)} players")
    elif event_name == 'metadata':
        last_metadata = data
        print(f"👤 Metadata updated for: {data.get('player_name', 'Unknown')}")
    
    # Emit to all connected web clients
    socketio.emit(event_name, data)

tcp_client = DCSHookClient(port=TCP_PORT, callback=handle_tcp_message)


# --- 5. HELPER FUNCTIONS ---
def load_json_file(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return default
    return default

def save_json_file(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

# Load Initial Config
_loaded_config = load_json_file(HUD_CONFIG_FILE, {})
if "profiles" not in _loaded_config:
    DEFAULT_SETTINGS = {
        "theme": "su25hmd", "color": "#00ff33", "brightness": 1.0, 
        "scale": 100, "offset_y": 0, "showDirector": True, "showWpInfo": True,
        "fov": 80
    }
    initial_data = _loaded_config if _loaded_config else DEFAULT_SETTINGS
    _loaded_config = { "current": "Default", "profiles": { "Default": initial_data } }
    save_json_file(HUD_CONFIG_FILE, _loaded_config)

hud_data = _loaded_config
clickable_mode_enabled = hud_data.get("clickable_enabled", False)
_map_settings_cache = load_json_file(MAP_CONFIG_FILE, {"distUnit": "nm", "altUnit": "ft"})
DEFAULT_HUD_SETTINGS = {
    "theme": "su25hmd", "color": "#00ff33", "brightness": 1.0, 
    "scale": 100, "offset_y": 0, "showDirector": True, "showWpInfo": True,
    "fov": 80
}

def get_current_settings():
    curr = hud_data.get("current", "Default")
    return hud_data["profiles"].get(curr, DEFAULT_HUD_SETTINGS)

def execute_ap_pulse(start_id, stop_id, axis, duration):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(str(start_id).encode(), DCS_INPUT_ADDR)
            socketio.sleep(duration) 
            s.sendto(str(stop_id).encode(), DCS_INPUT_ADDR)
    except Exception as e:
        print(f"Pulse Error: {e}")
    finally:
        ap_axis_locks[axis] = False

# --- 6. SOCKET EVENTS & FLASK ROUTES ---

# ... [Socket IO Handlers] ...
@socketio.on('toggleAP')
def handle_ap_toggle(data=None):
    if nav.ap_engaged:
        nav.disengage_ap()
        print("🤖 AP: DISENGAGED")
        socketio.emit('msg', "Autopilot OFF")
    else:
        success = nav.engage_ap()
        if success:
            print("🤖 AP: ENGAGED")
            socketio.emit('msg', "Autopilot ON")
        else:
            print("⚠️ AP Error: No Route Active")
            socketio.emit('msg', "AP Error: No Route")

@socketio.on('toggle_clickable')
def handle_toggle_clickable(data):
    global clickable_mode_enabled
    state = data.get('state', False)
    clickable_mode_enabled = state
    hud_data["clickable_enabled"] = state
    save_json_file(HUD_CONFIG_FILE, hud_data)
    print(f"👉 Clickable Cockpit: {'ENABLED' if state else 'DISABLED'}")
    socketio.emit('msg', f"Clickable Mode: {'ON' if state else 'OFF'}")
    if not state:
        socketio.emit('hover_status', {'active': False})

@socketio.on('mark_clickable_point')
def handle_mark_clickable(data):
    if not last_known_telemetry: return
    t = last_known_telemetry
    if 'self_pos' not in t or 'cam' not in t: return

    dist_cm = float(data.get('dist', 60))
    ac_pos = t['self_pos']
    ac_euler = { "hdg": t.get('hdg', 0), "pitch": t.get('pitch', 0), "roll": t.get('roll', 0) }
    cam_pos = t['cam']['p']
    cam_vec = t['cam']['x'] 
    
    body_point = MathUtils.calculate_body_relative_point(ac_pos, ac_euler, cam_pos, cam_vec, dist_cm)
    points = load_json_file(CLICKABLE_FILE, [])
    new_id = MathUtils.get_next_id(points)
    new_entry = {
        "id": new_id, "name": f"Switch_{new_id}",
        "x": body_point['x'], "y": body_point['y'], "z": body_point['z'],
        "dist_cm": dist_cm, "action": "LoSetCommand(0);", "desc": "Description"
    }
    points.append(new_entry)
    save_json_file(CLICKABLE_FILE, points)
    print(f"📍 SAVED Point {new_id}: {body_point}")
    socketio.emit('msg', f"Saved Point {new_id}")

@socketio.on('update_clickable_point')
def handle_update_point(data):
    p_id = data.get('id')
    points = load_json_file(CLICKABLE_FILE, [])
    found = False
    for p in points:
        if p.get('id') == p_id:
            p['name'] = data.get('name', p['name'])
            p['action_type'] = data.get('action_type', 'dcs')
            p['action_val'] = data.get('action_val', 0)
            found = True
            break
    if found:
        save_json_file(CLICKABLE_FILE, points)
        socketio.emit('msg', f"Updated {data.get('name')}")

@socketio.on('delete_clickable_point')
def handle_delete_point(data):
    p_id = data.get('id')
    points = load_json_file(CLICKABLE_FILE, [])
    new_list = [p for p in points if p.get('id') != p_id]
    save_json_file(CLICKABLE_FILE, new_list)
    socketio.emit('msg', f"Deleted Point {p_id}")

    socketio.emit('msg', f"Deleted Point {p_id}")

# --- POINTER BRIDGE (Phase 3.3) ---
virtual_pointer_state = { "active": False, "x": 0.5, "y": 0.5, "mode": "pct" } # Default center 50%

@socketio.on('virtual_pointer_update')
def handle_pointer_update(data):
    """ 
    Received from Overlay (InputManager).
    data: { 'dx': float, 'dy': float, 'mode': 'rel'/'abs'/'pct' }
    """
    global virtual_pointer_state
    
    mode = data.get('mode', 'rel')
    
    # Update State - Unify to Percentage (0.0 - 1.0)
    if mode == 'rel':
        # Assume relative moves are in pixels (e.g. from Joystick/Keys)
        # Normalize assuming a standard virtual canvas reference (e.g. 1920x1080)
        REF_W, REF_H = 1920.0, 1080.0
        SENSITIVITY = 1.0 
        
        dx_pct = (data.get('dx', 0) / REF_W) * SENSITIVITY
        dy_pct = (data.get('dy', 0) / REF_H) * SENSITIVITY
        
        current_x = virtual_pointer_state.get('x', 0.5)
        current_y = virtual_pointer_state.get('y', 0.5)
        
        # Determine if current state is pixels (legacy) or pct
        if current_x > 2.0: current_x /= REF_W
        if current_y > 2.0: current_y /= REF_H

        virtual_pointer_state['x'] = max(0.0, min(1.0, current_x + dx_pct))
        virtual_pointer_state['y'] = max(0.0, min(1.0, current_y + dy_pct))
        virtual_pointer_state['mode'] = 'pct'
        
    elif mode == 'abs':
        # Legacy absolute in pixels - treat as raw input for safety, but try to normalize if huge
        val_x = data.get('x', 0)
        val_y = data.get('y', 0)
        if val_x > 1.0: val_x /= 1920.0
        if val_y > 1.0: val_y /= 1080.0
        
        virtual_pointer_state['x'] = max(0.0, min(1.0, val_x))
        virtual_pointer_state['y'] = max(0.0, min(1.0, val_y))
        virtual_pointer_state['mode'] = 'pct'

    elif mode == 'pct':
        virtual_pointer_state['x'] = max(0.0, min(1.0, data.get('x', 0.5)))
        virtual_pointer_state['y'] = max(0.0, min(1.0, data.get('y', 0.5)))
        virtual_pointer_state['mode'] = 'pct'

    socketio.emit('pointer_update', virtual_pointer_state)

@socketio.on('toggle_pointer_mode')
def handle_pointer_toggle(data):
    global virtual_pointer_state
    
    new_state = data.get('active', False)
    virtual_pointer_state['active'] = new_state
    
    # RESET TO CENTER ON ACTIVATION
    if new_state:
        virtual_pointer_state['x'] = 0.5
        virtual_pointer_state['y'] = 0.5
        virtual_pointer_state['mode'] = 'pct'
        
    print(f"🖱️ Pointer Mode: {'ON' if virtual_pointer_state['active'] else 'OFF'}")
    socketio.emit('pointer_mode_changed', virtual_pointer_state)

@socketio.on('virtual_click')
def handle_virtual_click(data):
    # data: { 'action': 'click' / 'down' / 'up' }
    print(f"📤 Relaying click to frontend: {data}")
    # Pass through to frontend
    socketio.emit('pointer_click_event', data)

@socketio.on('interact_at_mouse')
def handle_interaction(data=None):
    if not clickable_mode_enabled or not last_known_telemetry: return

    mouse_global = InputManager.get_cursor_position()
    if not mouse_global: return
        
    settings = get_current_settings() 
    win_w = int(settings.get('win_w', 1920))
    win_h = int(settings.get('win_h', 1080))
    win_x = int(settings.get('win_x', 0))
    win_y = int(settings.get('win_y', 0))
    fov = float(settings.get('fov', 80.0))
    mouse_local = (mouse_global[0] - win_x, mouse_global[1] - win_y)

    t = last_known_telemetry
    points = load_json_file(CLICKABLE_FILE, [])
    cam_pos = t['cam']['p']
    cam_fwd = t['cam']['x'] 
    
    hit_radius = CLICK_HIT_RADIUS if 'CLICK_HIT_RADIUS' in globals() else 20
    hit_found = None
    closest_dist = 9999

    for pt in points:
        body_offset = {'x': pt.get('x',0), 'y': pt.get('y',0), 'z': pt.get('z',0)}
        plane_hpb = {'heading': t['hdg'], 'pitch': t['pitch'], 'bank': t['roll']}
        world_pos = MathUtils.get_world_position(t['self_pos'], plane_hpb, body_offset)

        rel = MathUtils.vec_sub(world_pos, cam_pos)
        local_x = rel['x'] * cam_fwd['x'] + rel['y'] * cam_fwd['y'] + rel['z'] * cam_fwd['z']
        
        if local_x <= 0: continue 

        screen_pt = MathUtils.world_to_screen(world_pos, t['cam'], (win_w, win_h), fov)
        if screen_pt:
            dist = math.hypot(screen_pt['x'] - mouse_local[0], screen_pt['y'] - mouse_local[1])
            if dist < hit_radius and dist < closest_dist:
                closest_dist = dist
                hit_found = pt

    if hit_found:
        print(f"\n>>> INTERACTION: {hit_found['name']}")
        act_type = hit_found.get('action_type', 'dcs')
        act_val = hit_found.get('action_val', 0)
        
        if act_type == 'dcs':
            try:
                cmd_id = str(act_val)
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(cmd_id.encode(), DCS_INPUT_ADDR)
                print(f"    ✅ Sent DCS Command: {cmd_id}")
                socketio.emit('msg', f"Action: {hit_found['name']}")
            except Exception as e:
                print(f"    ❌ Socket Error: {e}")
        elif act_type == 'app' or act_type == 'function':
            if act_val == "engageAP": handle_ap_toggle()
            elif act_val == "mark_target": handle_mark_look_point()
            elif act_val == "cycle_next": handle_cycle_wp({'dir': 1})
            elif act_val == "cycle_prev": handle_cycle_wp({'dir': -1})
            elif act_val == "restore_route": handle_restore_last_route()
            elif act_val == "set_active_poi": handle_activate_last_poi()
            elif act_val == "toggle_hud": socketio.emit('toggle_hud_visibility') 
            else:
                print(f"    ⚠️ Unmapped Function: {act_val}")
                socketio.emit('msg', f"Unknown Func: {act_val}")

@socketio.on('connect')
def handle_connect():
    socketio.emit('apply_settings', get_current_settings())
    socketio.emit('server_handshake', {'boot_id': SERVER_BOOT_ID})
    if nav.route and len(nav.route) > 0:
        socketio.emit('force_route_sync', {
            'route': nav.route,
            'index': nav.active_wp_index,
            'name': active_route_name or "Server Route"
        })
    # Send current phonebook to new client
    if phonebook:
        socketio.emit('phonebook', phonebook)
    # Send cached metadata to new client
    if last_metadata:
        socketio.emit('metadata', last_metadata)

@socketio.on('dcs_loop_start')
def handle_loop_start(data):
    cmd_id = int(data.get('id', 0))
    if cmd_id > 0:
        active_command_loops.add(cmd_id)

@socketio.on('dcs_loop_stop')
def handle_loop_stop(data):
    cmd_id = int(data.get('id', 0))
    if cmd_id in active_command_loops:
        active_command_loops.remove(cmd_id)

@socketio.on('mark_look_point')
def handle_mark_look_point(data=None):
    global valid_look_cache
    global tgt_sequence_id 
    print("🔭 TRIGGER: Sending Raycast + Visual A-G Toggle...")
    try:
        dcs_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dcs_sock.sendto("10001".encode(), DCS_INPUT_ADDR)
        socketio.sleep(0.05)
        dcs_sock.sendto("111".encode(), DCS_INPUT_ADDR) 
    except: return
    
    socketio.sleep(0.25) 
    lat, lon, alt = valid_look_cache['lat'], valid_look_cache['lon'], valid_look_cache['alt']
    
    if lat == 0 and lon == 0:
        print("⚠️ MARK FAILED: No valid Look Data received yet.")
        return

    timestamp = int(time.time())
    poi_name = f"T{tgt_sequence_id}"
    new_poi = { "lat": lat, "lon": lon, "alt": alt, "name": poi_name, "color": "#e74c3c", "sidc": "SHGPU-------", "source": "visual", "time": timestamp }

    tgt_sequence_id += 1 
    print(f"🎯 MARKER: Sending {poi_name} to Client")
    socketio.emit('visual_target_added', new_poi)

@socketio.on('update_pois')
def handle_poi_sync(data):
    save_json_file(POIS_FILE, data)
    socketio.emit('pois_update', data)    

@socketio.on('update_settings')
def handle_settings_update(data):
    curr = hud_data["current"]
    if curr not in hud_data["profiles"]: hud_data["profiles"][curr] = DEFAULT_HUD_SETTINGS.copy()
    hud_data["profiles"][curr].update(data); save_json_file(HUD_CONFIG_FILE, hud_data)
    socketio.emit('apply_settings', hud_data["profiles"][curr])

@socketio.on('set_active_wp')
def handle_set_active(data):
    global last_standard_route_cache, active_route_name 
    route = data.get('route', [])
    index = data.get('index', -1)
    name = data.get('name', None) 
    if name: active_route_name = name
    if route and len(route) > 0:
        last_standard_route_cache = {"route": route, "index": index}
    nav.active_wp_index = index
    nav.route = route
    tgt_sequence_id = 1
    socketio.emit('force_route_sync', {
        'route': nav.route,
        'index': nav.active_wp_index,
        'name': active_route_name or "Active Route"
    })

@socketio.on('cycle_wp')
def handle_cycle_wp(data):
    new_idx = nav.cycle_waypoint(data.get('dir', 1))
    if new_idx is not None: socketio.emit('seq_update', {'index': new_idx})

@socketio.on('sync_measurement')
def handle_measurement_sync(data):
    socketio.emit('remote_measurement', data, include_self=False)

@socketio.on('dcs_cmd')
def handle_dcs_cmd(data):
    cmd_id = data.get('id')
    if cmd_id:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(f"{cmd_id}".encode(), DCS_INPUT_ADDR)

@socketio.on('dcs_multi_cmd')
def handle_dcs_multi_command(data):
    cmd_id = data.get('id')
    count = data.get('count', 10) 
    if cmd_id:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            for _ in range(count):
                s.sendto(f"{cmd_id}".encode(), DCS_INPUT_ADDR)
                socketio.sleep(0.02) 

@socketio.on('dcs_key')
def handle_dcs_key(data):
    key_name = data.get('key')
    print(f"⌨️  Server received key request: {key_name}")
    try:
        keyboard.press(key_name); time.sleep(0.1); keyboard.release(key_name)
    except Exception as e: print(f"❌ Key Emulation Error: {e}")

# ... [Flask Routes] ...
@app.route('/api/clickable_points', methods=['GET'])
def get_clickable_points(): return jsonify(load_json_file(CLICKABLE_FILE, []))

@app.route('/api/pois', methods=['GET'])
def get_pois(): return jsonify(load_json_file(POIS_FILE, []))

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({ 
        "current_profile": hud_data["current"], 
        "profiles_list": list(hud_data["profiles"].keys()), 
        "settings": get_current_settings(),
        "clickable_enabled": hud_data.get("clickable_enabled", False) 
    })

@app.route('/api/profiles/create', methods=['POST'])
def create_profile():
    name = request.json.get('name')
    if not name: return jsonify({"error": "No name"}), 400
    hud_data["profiles"][name] = get_current_settings().copy(); hud_data["current"] = name; save_json_file(HUD_CONFIG_FILE, hud_data)
    socketio.emit('apply_settings', get_current_settings())
    return jsonify({"status": "created", "name": name})

@app.route('/api/profiles/select', methods=['POST'])
def select_profile():
    name = request.json.get('name')
    if name in hud_data["profiles"]:
        hud_data["current"] = name; save_json_file(HUD_CONFIG_FILE, hud_data)
        socketio.emit('apply_settings', get_current_settings())
        return jsonify({"status": "selected", "settings": get_current_settings()})
    return jsonify({"error": "Profile not found"}), 404

@app.route('/api/profiles/delete', methods=['POST'])
def delete_profile():
    name = request.json.get('name')
    if name == "Default": return jsonify({"error": "Cannot delete Default"}), 400
    if name in hud_data["profiles"]:
        del hud_data["profiles"][name]
        if hud_data["current"] == name: hud_data["current"] = "Default"; socketio.emit('apply_settings', get_current_settings())
        save_json_file(HUD_CONFIG_FILE, hud_data); return jsonify({"status": "deleted", "current": hud_data["current"]})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/hud_profiles', methods=['GET'])
def get_hud_profiles():
    profiles_dir = os.path.join(app.root_path, 'static', 'hud_profiles')
    if not os.path.exists(profiles_dir): os.makedirs(profiles_dir); return jsonify([])
    return jsonify(sorted([f.replace('.js', '') for f in os.listdir(profiles_dir) if f.endswith('.js')]))

@app.route('/api/routes', methods=['GET'])
def get_routes(): return jsonify(load_json_file(ROUTES_FILE, {}))

@app.route('/api/routes', methods=['POST'])
def save_library():
    data = request.json
    save_json_file(ROUTES_FILE, data)
    socketio.emit('routes_library_update', data)
    return jsonify({"status": "saved", "count": len(data)})

@app.route('/api/routes/<name>', methods=['DELETE'])
def delete_route(name):
    db = load_json_file(ROUTES_FILE, {})
    if name in db: 
        del db[name]
        save_json_file(ROUTES_FILE, db)
    socketio.emit('routes_library_update', db)
    return jsonify(db)

@app.route('/api/airports', methods=['GET'])
def get_airports(): return jsonify(load_json_file(os.path.join(DATA_DIR, 'airports.json'), {}))   

@app.route('/api/map/settings', methods=['GET'])
def get_map_settings():
    default_vis = { 
        "airports": True, "units": True, "alt": True, "hdg": True, "hud": False,
        "grid": True, "mgrs": False, "liveAir": False, 
        "units_air": True, "units_ground": True, "units_naval": True, "units_static": False,
        "units_red": True, "units_blue": True, "units_neutral": True,
        "pois": True, "threats": True, "wakeLock": False
    }
    default_map = { 
        "coords": "latlon", "altUnit": "ft", "distUnit": "nm", "defAlt": 2000, 
        "layer": "dark", "uiScale": "1.0", "visibleRoutes": [], 
        "vis": default_vis 
    }
    
    data = load_json_file(MAP_CONFIG_FILE, default_map)
    
    # Robust Merge for 'vis' to handle old config files
    if "vis" not in data: data["vis"] = default_vis
    else:
        for k, v in default_vis.items():
            if k not in data["vis"]: data["vis"][k] = v
            
    return jsonify(data)

@app.route('/api/map/settings', methods=['POST'])
def save_map_settings():
    global _map_settings_cache
    data = request.json
    save_json_file(MAP_CONFIG_FILE, data)
    _map_settings_cache = data
    socketio.emit('map_settings_update', data)
    if tcp_client and tcp_client.running:
        tcp_client.send_packet({ "type": "config", "vis": data.get("vis", {}) })
    return jsonify({"status": "saved", "settings": data})      

@socketio.on('activate_poi_route')
def handle_activate_poi_route(data):
    """ Loads all Visual POIs as the active navigation route. """
    global active_route_name, last_standard_route_cache
    target_index = data.get('index', 0)
    pois = load_json_file(POIS_FILE, [])
    if not pois: return
    
    is_already_visual = (len(nav.route) > 0 and nav.route[0].get('type') == 'poi')
    if not is_already_visual and len(nav.route) > 0:
        last_standard_route_cache = {"route": nav.route, "index": nav.active_wp_index}

    route_data = []
    for i, p in enumerate(pois):
        p_copy = p.copy(); p_copy['type'] = 'poi'; p_copy['name'] = f"T{i + 1}"
        route_data.append(p_copy)
        
    nav.route = route_data
    nav.active_wp_index = target_index
    socketio.emit('force_route_sync', { 'route': route_data, 'index': target_index, 'name': "Visual Targets" })
    socketio.emit('msg', f"Tactical Mode: T{target_index+1} Active")

def perform_nav_stop():
    global active_route_name 
    nav.route = []
    nav.active_wp_index = -1
    active_route_name = None
    socketio.emit('force_route_sync', { 'route': [], 'index': -1, 'name': "Route Cleared" })
    socketio.emit('msg', "Navigation Stopped")
    print("🛑 HUD: Navigation Disengaged")

@socketio.on('restore_last_route')
def handle_restore_last_route():
    global last_standard_route_cache
    is_running_standard = (len(nav.route) > 0 and nav.route[0].get('type') != 'poi')
    if is_running_standard: perform_nav_stop(); return
    if not last_standard_route_cache["route"]: print("No previous route to restore."); return
    nav.route = last_standard_route_cache["route"]
    idx = last_standard_route_cache["index"]
    if idx >= len(nav.route): idx = 0
    nav.active_wp_index = idx
    socketio.emit('force_route_sync', { 'route': nav.route, 'index': idx, 'name': "Restored Route" })
    print(f"🔄 HUD: Restored Standard Route")

@socketio.on('activate_last_poi')
def handle_activate_last_poi():
    is_running_visual = (len(nav.route) > 0 and nav.route[0].get('type') == 'poi')
    if is_running_visual: perform_nav_stop(); return
    pois = load_json_file(POIS_FILE, [])
    if not pois: return
    handle_activate_poi_route({'index': len(pois) - 1})

@app.route('/')
def map_page(): return render_template('map.html')
@app.route('/hud')
def hud_page(): return render_template('hud.html')
@app.route('/static/<path:filename>')
def serve_static(filename): return send_from_directory(os.path.join(app.root_path, 'static'), filename)    


# --- 7. LEGACY THREADS & LISTENERS ---
def udp_listener():
    global last_known_telemetry, valid_look_cache
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(0)
    sender_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"📡 UDP Listener active on {UDP_PORT}")
    frame_count = 0 
    
    while True:
        try:
            batch_telemetry = None 
            while True:
                try: 
                    data, _ = sock.recvfrom(65535)
                    decoded = data.decode('utf-8')
                    if tcp_client: tcp_client.set_udp_alive() # WAKE TCP
                    
                    if '"type":"units"' in decoded: 
                        socketio.emit('tactical', json.loads(decoded))
                        continue
                    tel = json.loads(decoded)
                    if tel.get('type') == 'player':
                        l_lat = float(tel.get('look_lat', 0))
                        l_lon = float(tel.get('look_lon', 0))
                        if l_lat != 0 and l_lon != 0:
                            valid_look_cache['lat'] = l_lat; valid_look_cache['lon'] = l_lon
                            valid_look_cache['alt'] = float(tel.get('look_alt', 0))
                            valid_look_cache['time'] = time.time()
                        batch_telemetry = tel 
                except BlockingIOError: break 
            
            if batch_telemetry:
                last_known_telemetry.update(batch_telemetry)
                steer = nav.calculate(batch_telemetry, _map_settings_cache)
                frame_count += 1
                if steer and steer.get('ap_status', False):
                    roll_strength = float(steer.get('pid_roll_out', 0.0))
                    pitch_strength = float(steer.get('pid_pitch_out', 0.0))
                    calc_roll_dur = max(0.02, min(0.2, abs(roll_strength) * 0.2))
                    calc_pitch_dur = max(0.02, min(0.1, abs(pitch_strength) * 0.05))

                    if not ap_axis_locks['roll'] and abs(roll_strength) > 0.05:
                        key = "ROLL_RIGHT" if roll_strength > 0 else "ROLL_LEFT"
                        if key in AP_KEY_MAP:
                            pair = AP_KEY_MAP[key]
                            ap_axis_locks['roll'] = True
                            socketio.start_background_task(execute_ap_pulse, pair[0], pair[1], 'roll', calc_roll_dur)

                    global last_pitch_time
                    current_time = time.time()
                    if (current_time - last_pitch_time) > 0.15:
                        if not ap_axis_locks['pitch'] and abs(pitch_strength) > 0.07:
                            key = "PITCH_UP" if pitch_strength > 0 else "PITCH_DOWN"
                            if key in AP_KEY_MAP:
                                pair = AP_KEY_MAP[key]
                                ap_axis_locks['pitch'] = True
                                socketio.start_background_task(execute_ap_pulse, pair[0], pair[1], 'pitch', calc_pitch_dur)
                                last_pitch_time = current_time

                    if steer.get('ap_cmd') and "SAFETY_RESET" in steer['ap_cmd']:
                         if "SAFETY_RESET" in AP_KEY_MAP:
                             dcs_id = AP_KEY_MAP["SAFETY_RESET"][0]
                             sender_sock.sendto(str(dcs_id).encode(), DCS_INPUT_ADDR)
                
                if steer and steer.get('sequenced'): 
                    socketio.emit('seq_update', {'index': nav.active_wp_index})
                batch_telemetry['steer'] = steer
                socketio.emit('telemetry', batch_telemetry)

            socketio.sleep(0.01)
        except Exception as e: 
            print(f"UDP Loop Error: {e}")
            socketio.sleep(0.01)

def command_looper(): 
    global active_command_loops
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            if active_command_loops:
                for cmd_id in list(active_command_loops):
                    msg = f"{cmd_id}".encode()
                    udp_sock.sendto(msg, DCS_INPUT_ADDR)
            time.sleep(0.25)
        except: time.sleep(1)

def hover_loop():
    print("👀 Hover Detector Started")
    cached_points = []
    last_cache_time = 0
    while True:
        try:
            if not clickable_mode_enabled:
                socketio.sleep(2) 
                continue

            if time.time() - last_cache_time > 2.0:
                cached_points = load_json_file(CLICKABLE_FILE, [])
                last_cache_time = time.time()

            if not last_known_telemetry or not cached_points:
                socketio.sleep(0.1); continue

            mouse_global = InputManager.get_cursor_position()
            if not mouse_global: socketio.sleep(0.1); continue

            settings = get_current_settings()
            win_w = int(settings.get('win_w', 1920))
            win_h = int(settings.get('win_h', 1080))
            win_x = int(settings.get('win_x', 0))
            win_y = int(settings.get('win_y', 0))
            fov = float(settings.get('fov', 80.0))
            mx_local = mouse_global[0] - win_x
            my_local = mouse_global[1] - win_y

            t = last_known_telemetry
            cam_pos = t['cam']['p']
            cam_fwd = t['cam']['x']
            closest_dist = CLICK_HIT_RADIUS if 'CLICK_HIT_RADIUS' in globals() else 20
            found_pt = None

            for pt in cached_points:
                body_offset = {'x': pt.get('x',0), 'y': pt.get('y',0), 'z': pt.get('z',0)}
                plane_hpb = {'heading': t['hdg'], 'pitch': t['pitch'], 'bank': t['roll']}
                world_pos = MathUtils.get_world_position(t['self_pos'], plane_hpb, body_offset)
                rel = MathUtils.vec_sub(world_pos, cam_pos)
                depth = rel['x']*cam_fwd['x'] + rel['y']*cam_fwd['y'] + rel['z']*cam_fwd['z']
                if depth <= 0: continue 

                screen_pt = MathUtils.world_to_screen(world_pos, t['cam'], (win_w, win_h), fov)
                if screen_pt:
                    dist = math.hypot(screen_pt['x'] - mx_local, screen_pt['y'] - my_local)
                    if dist < closest_dist:
                        closest_dist = dist
                        found_pt = pt

            if found_pt:
                label = found_pt.get('name')
                if not label or label == "New Point":
                    val = found_pt.get('action_val', '')
                    label = str(val) if val else f"ID {found_pt.get('id')}"
                socketio.emit('hover_status', { 'active': True, 'x': mx_local, 'y': my_local, 'label': label })
            else:
                socketio.emit('hover_status', {'active': False})
            socketio.sleep(0.016)
        except Exception as e:
            print(f"Hover Loop Error: {e}")
            socketio.sleep(1.0)


# --- 8. MAIN EXECUTION ---
if __name__ == '__main__':
    socketio.start_background_task(udp_listener)
    socketio.start_background_task(command_looper)
    socketio.start_background_task(hover_loop)
    
    # 2. Start TCP Module
    tcp_client.start()
    
    print(f"🌍 SERVER RUNNING: http://127.0.0.1:{WEB_PORT}")
    
    overlay_process = None
    overlay_path = os.path.join("modules", "overlay.py")
    if os.path.exists(overlay_path):
        print("🚀 Launching HUD Overlay...")
        overlay_process = subprocess.Popen([sys.executable, overlay_path])
    
    def cleanup():
        if overlay_process: overlay_process.terminate()
        tcp_client.stop()
            
    atexit.register(cleanup)
    
    try:
        socketio.run(app, host='0.0.0.0', port=WEB_PORT)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()