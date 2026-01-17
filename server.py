# server.py 
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO
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
from modules.nav_computer import NavComputer
from modules.utils import MathUtils
from modules.mouse_tracker import MouseTracker

# --- CONFIGURATION ---
UDP_IP = "127.0.0.1"
UDP_PORT = 11000
DCS_INPUT_ADDR = ("127.0.0.1", 11001)
WEB_PORT = 5000
SERVER_BOOT_ID = time.time()
CLICK_HIT_RADIUS = 13

# ---# TCP Configuration (Theater Data)
TCP_IP = '0.0.0.0'
TCP_PORT = 11002
tcp_client_socket = None # Store active connection to push config updates


# CHANGE THESE LINES:
DATA_DIR = "DATA"  # Define the folder name
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

ROUTES_FILE = os.path.join(DATA_DIR, "saved_routes.json")
HUD_CONFIG_FILE = os.path.join(DATA_DIR, "hud_config.json")
MAP_CONFIG_FILE = os.path.join(DATA_DIR, "map_config.json")
POIS_FILE = os.path.join(DATA_DIR, "saved_pois.json")
CLICKABLE_FILE = os.path.join(DATA_DIR, "clickable_point_data.json")

# --- GLOBAL VARS ---                  
last_known_telemetry = {}
captured_look_data = None
valid_look_cache = {"lat": 0, "lon": 0, "alt": 0, "time": 0}
tgt_sequence_id = 1
last_standard_route_cache = {"route": [], "index": -1}
active_route_name = None
active_command_loops = set()
clickable_mode_enabled = False
last_pitch_time = 0

# --- DCS COMMAND MAPPING (Start, Stop) ---
# Format: "COMMAND_NAME": (START_ID, STOP_ID)
AP_KEY_MAP = {
    "PITCH_UP":   (195, 196), # iCommandPlaneUpStart / Stop
    "PITCH_DOWN": (193, 194), # iCommandPlaneDownStart / Stop
    "ROLL_LEFT":  (197, 198), # iCommandPlaneLeftStart / Stop
    "ROLL_RIGHT": (199, 200)  # iCommandPlaneRightStart / Stop
}

ap_axis_locks = {
    "pitch": False,
    "roll": False
}
# --- FLASK SETUP ---
app = Flask(__name__, static_folder='state')
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='gevent')

# --- PERSISTENCE HELPERS ---
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

# --- MASTER STATE ---
DEFAULT_SETTINGS = {
    "theme": "su25hmd", "color": "#00ff33", "brightness": 1.0, 
    "scale": 100, "offset_y": 0, "showDirector": True, "showWpInfo": True,
    "fov": 80
}

_loaded_config = load_json_file(HUD_CONFIG_FILE, {})
if "profiles" not in _loaded_config:
    initial_data = _loaded_config if _loaded_config else DEFAULT_SETTINGS
    _loaded_config = { "current": "Default", "profiles": { "Default": initial_data } }
    save_json_file(HUD_CONFIG_FILE, _loaded_config)

hud_data = _loaded_config
clickable_mode_enabled = hud_data.get("clickable_enabled", False)
_map_settings_cache = load_json_file(MAP_CONFIG_FILE, {"distUnit": "nm", "altUnit": "ft"})

def get_current_settings():
    curr = hud_data.get("current", "Default")
    return hud_data["profiles"].get(curr, DEFAULT_SETTINGS)

# ---   NAV COMP    ---
nav = NavComputer()

@socketio.on('toggleAP')
def handle_ap_toggle(data=None):
    if nav.ap_engaged:
        nav.disengage_ap()
        print("🤖 AP: DISENGAGED")
        socketio.emit('msg', "Autopilot OFF")
    else:
        # Only engage if we have a route
        success = nav.engage_ap()
        if success:
            print("🤖 AP: ENGAGED")
            socketio.emit('msg', "Autopilot ON")
        else:
            print("⚠️ AP Error: No Route Active")
            socketio.emit('msg', "AP Error: No Route")

#   --- CLICKABLE   ---
# --- CLICKABLE COCKPIT LOGIC ---

@socketio.on('toggle_clickable')
def handle_toggle_clickable(data):
    global clickable_mode_enabled
    state = data.get('state', False)
    clickable_mode_enabled = state
    
    # 1. Save to File (Persistence)
    hud_data["clickable_enabled"] = state
    save_json_file(HUD_CONFIG_FILE, hud_data)

    print(f"👉 Clickable Cockpit: {'ENABLED' if state else 'DISABLED'}")
    socketio.emit('msg', f"Clickable Mode: {'ON' if state else 'OFF'}")
    
    # 2. Clear Visuals if Disabled
    if not state:
        socketio.emit('hover_status', {'active': False})

@socketio.on('mark_clickable_point')
def handle_mark_clickable(data):
    # 1. Validation
    if not last_known_telemetry:
        print("⚠️ Error: No Telemetry Data")
        return
        
    t = last_known_telemetry
    
    # Check if we have all necessary components
    # We need: self_pos (x,y,z), cam (p, x-vector), attitude (hdg, pitch, roll)
    if 'self_pos' not in t or 'cam' not in t:
        print("⚠️ Error: Missing Position/Camera Data in Telemetry")
        return

    dist_cm = float(data.get('dist', 60))
    
    # 2. Extract Data for MathUtils
    # DCS Export sends:
    #   t['self_pos'] -> {x, y, z}
    #   t['cam']['p'] -> {x, y, z} (Position)
    #   t['cam']['x'] -> {x, y, z} (Forward Vector)
    
    ac_pos = t['self_pos']
    ac_euler = {
        "hdg": t.get('hdg', 0),
        "pitch": t.get('pitch', 0),
        "roll": t.get('roll', 0)
    }
    cam_pos = t['cam']['p']
    cam_vec = t['cam']['x'] # 'x' is the forward vector in DCS camera matrix
    
    # 3. Perform Calculation
    body_point = MathUtils.calculate_body_relative_point(
        ac_pos, ac_euler, cam_pos, cam_vec, dist_cm
    )
    
    # 4. Save to File
    points = load_json_file(CLICKABLE_FILE, [])
    new_id = MathUtils.get_next_id(points)
    
    new_entry = {
        "id": new_id,
        "name": f"Switch_{new_id}",
        "x": body_point['x'],
        "y": body_point['y'],
        "z": body_point['z'],
        "dist_cm": dist_cm,
        "action": "LoSetCommand(0);", # Default placeholder
        "desc": "Description"
    }
    
    points.append(new_entry)
    save_json_file(CLICKABLE_FILE, points)
    
    print(f"📍 SAVED Point {new_id}: {body_point}")
    socketio.emit('msg', f"Saved Point {new_id}")
    
    # Force overlay list refresh?
    # socketio.emit('refresh_clickable_list')

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
        print(f"✅ Updated Point {p_id}")
        socketio.emit('msg', f"Updated {data.get('name')}")

@socketio.on('delete_clickable_point')
def handle_delete_point(data):
    p_id = data.get('id')
    points = load_json_file(CLICKABLE_FILE, [])
    
    # Filter out the deleted ID
    new_list = [p for p in points if p.get('id') != p_id]
    
    save_json_file(CLICKABLE_FILE, new_list)
    print(f"🗑️ Deleted Point {p_id}")
    socketio.emit('msg', f"Deleted Point {p_id}")

# [SEARCH STRING] @socketio.on('interact_at_mouse')# [SEARCH STRING] @socketio.on('interact_at_mouse')
@socketio.on('interact_at_mouse')
def handle_interaction(data=None):
    if not clickable_mode_enabled:
        return
    if not last_known_telemetry: return

    # 1. MOUSE & SCREEN CALCS
    mouse_global = MouseTracker.get_cursor_position()
    if not mouse_global: return
        
    settings = get_current_settings() 
    win_w = int(settings.get('win_w', 1920))
    win_h = int(settings.get('win_h', 1080))
    win_x = int(settings.get('win_x', 0))
    win_y = int(settings.get('win_y', 0))
    fov = float(settings.get('fov', 80.0))
    
    # Mouse relative to DCS window
    mouse_local = (mouse_global[0] - win_x, mouse_global[1] - win_y)

    # 2. CHECK HITS
    t = last_known_telemetry
    points = load_json_file(CLICKABLE_FILE, [])
    
    plane_pos = t['self_pos']
    cam_pos = t['cam']['p']
    cam_fwd = t['cam']['x'] 
    
    # Load Tolerance from config or default to 60px
    hit_radius = CLICK_HIT_RADIUS if 'CLICK_HIT_RADIUS' in globals() else 20

    hit_found = None
    closest_dist = 9999

    for pt in points:
        # Reconstruct World Position
        body_offset = {'x': pt.get('x',0), 'y': pt.get('y',0), 'z': pt.get('z',0)}
        plane_hpb = {'heading': t['hdg'], 'pitch': t['pitch'], 'bank': t['roll']}
        world_pos = MathUtils.get_world_position(plane_pos, plane_hpb, body_offset)

        # Basic depth check
        rel = MathUtils.vec_sub(world_pos, cam_pos)
        local_x = rel['x'] * cam_fwd['x'] + rel['y'] * cam_fwd['y'] + rel['z'] * cam_fwd['z']
        
        if local_x <= 0: continue # Behind camera

        # Project to Screen
        screen_pt = MathUtils.world_to_screen(world_pos, t['cam'], (win_w, win_h), fov)
        
        if screen_pt:
            dx = screen_pt['x'] - mouse_local[0]
            dy = screen_pt['y'] - mouse_local[1]
            dist = math.hypot(dx, dy)
            
            # Check against buffer radius
            if dist < hit_radius and dist < closest_dist:
                closest_dist = dist
                hit_found = pt

    # 3. EXECUTE ACTION
    if hit_found:
        print(f"\n>>> INTERACTION: {hit_found['name']}")
        
        # Overlay sends 'dcs' or 'app'
        act_type = hit_found.get('action_type', 'dcs')
        act_val = hit_found.get('action_val', 0)
        
        print(f"    Type: {act_type} | Val: {act_val}")

        # --- A. DCS COMMANDS ---
        if act_type == 'dcs':
            try:
                cmd_id = str(act_val)
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(cmd_id.encode(), DCS_INPUT_ADDR)
                print(f"    ✅ Sent DCS Command: {cmd_id}")
                socketio.emit('msg', f"Action: {hit_found['name']}")
            except Exception as e:
                print(f"    ❌ Socket Error: {e}")

        # --- B. APP FUNCTIONS ---
        # Matches the keys in your overlay 'hotkeys' list
        elif act_type == 'app' or act_type == 'function':
            
            # MAP: UI Name -> Server Function
            if act_val == "engageAP":
                handle_ap_toggle()
            
            elif act_val == "mark_target":
                handle_mark_look_point()
                
            elif act_val == "cycle_next":
                 handle_cycle_wp({'dir': 1})
            
            elif act_val == "cycle_prev":
                 handle_cycle_wp({'dir': -1})
                 
            elif act_val == "restore_route":
                handle_restore_last_route()

            elif act_val == "set_active_poi":
                handle_activate_last_poi()

            elif act_val == "toggle_hud":
                # Server doesn't toggle HUD directly, but can msg client
                socketio.emit('toggle_hud_visibility') 

            else:
                print(f"    ⚠️ Unmapped Function: {act_val}")
                socketio.emit('msg', f"Unknown Func: {act_val}")
    else:
        # Optional: Print only if debugging
        print(">>> No hit")
        pass
    
@app.route('/api/clickable_points', methods=['GET'])
def get_clickable_points():
    return jsonify(load_json_file(CLICKABLE_FILE, []))


# --- SOCKET EVENTS ---
@socketio.on('connect')
def handle_connect():
    # 1. Send settings
    socketio.emit('apply_settings', get_current_settings())
    
    # 2. NEW: Send the Server Boot ID so client knows if we restarted
    socketio.emit('server_handshake', {'boot_id': SERVER_BOOT_ID})

    # 3. Send Active Route State (Keep your existing code here)
    if nav.route and len(nav.route) > 0:
        socketio.emit('force_route_sync', {
            'route': nav.route,
            'index': nav.active_wp_index,
            'name': active_route_name or "Server Route"
        })

#   --- keybing tester
@socketio.on('dcs_loop_start')
def handle_loop_start(data):
    cmd_id = int(data.get('id', 0))
    if cmd_id > 0:
        active_command_loops.add(cmd_id)
        # print(f"🔥 Starting Loop for {cmd_id}")

@socketio.on('dcs_loop_stop')
def handle_loop_stop(data):
    cmd_id = int(data.get('id', 0))
    if cmd_id in active_command_loops:
        active_command_loops.remove(cmd_id)
        # print(f"🛑 Stopping Loop for {cmd_id}")

# --- VISUAL TARGETING LOGIC ---
@socketio.on('mark_look_point')
def handle_mark_look_point(data=None):
    """ Called when user presses the Mark Key """
    global valid_look_cache
    global tgt_sequence_id 
    
    print("🔭 TRIGGER: Sending Raycast + Visual A-G Toggle...")
    
    try:
        dcs_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 1. Request Raycast (Send ID only)
        dcs_sock.sendto("10001".encode(), DCS_INPUT_ADDR)
        
        # 2. Toggle Laser/AG Mode (Send ID only - simulates click)
        socketio.sleep(0.05)
        dcs_sock.sendto("111".encode(), DCS_INPUT_ADDR) 
        
    except Exception as e:
        print(f"Socket Error: {e}")
        return
    
    # 3. Wait for Lua to process and UDP listener to cache the result
    socketio.sleep(0.25) 
    
    # 4. READ FROM CACHE
    lat = valid_look_cache['lat']
    lon = valid_look_cache['lon']
    alt = valid_look_cache['alt']
    
    # Check if cache is empty (e.g. user hasn't looked at anything yet)
    if lat == 0 and lon == 0:
        print("⚠️ MARK FAILED: No valid Look Data received yet.")
        return

    # 5. Create POI Data
    timestamp = int(time.time())
    poi_name = f"T{tgt_sequence_id}"
    
    new_poi = {
        "lat": lat, "lon": lon, "alt": alt, 
        "name": poi_name, "color": "#e74c3c", 
        "sidc": "SHGPU-------", "source": "visual",
        "time": timestamp
    }

    # 6. Increment Sequence
    tgt_sequence_id += 1 

    # 7. SEND TO CLIENT (Client acts as the Brain and saves to the active mission)
    print(f"🎯 MARKER: Sending {poi_name} to Client")
    socketio.emit('visual_target_added', new_poi)

@socketio.on('update_pois')
def handle_poi_sync(data):
    save_json_file(POIS_FILE, data)
    socketio.emit('pois_update', data)    

@socketio.on('update_settings')
def handle_settings_update(data):
    curr = hud_data["current"]
    if curr not in hud_data["profiles"]: hud_data["profiles"][curr] = DEFAULT_SETTINGS.copy()
    hud_data["profiles"][curr].update(data); save_json_file(HUD_CONFIG_FILE, hud_data)
    socketio.emit('apply_settings', hud_data["profiles"][curr])

@socketio.on('set_active_wp')
def handle_set_active(data):
    """ Standard Route Activation """
    global last_standard_route_cache
    global active_route_name 
    
    route = data.get('route', [])
    index = data.get('index', -1)
    name = data.get('name', None) 
    
    if name:
        active_route_name = name

    if route and len(route) > 0:
        last_standard_route_cache = {"route": route, "index": index}
        
    nav.active_wp_index = index
    nav.route = route
    tgt_sequence_id = 1
    
    # 📢 BROADCAST: Sync this new route to ALL clients immediately
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
    # Relay measurement data to all OTHER clients
    # include_self=False because the sender already drew the line
    socketio.emit('remote_measurement', data, include_self=False)

# DCS COMMAND HANDLERS
DCS_INPUT_ADDR = ("127.0.0.1", 11001)

@socketio.on('dcs_cmd')
def handle_dcs_cmd(data):
    # We only care about the ID now. 
    cmd_id = data.get('id')
    if cmd_id:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(f"{cmd_id}".encode(), DCS_INPUT_ADDR)

@socketio.on('dcs_multi_cmd')
def handle_dcs_multi_command(data):
    cmd_id = data.get('id')
    count = data.get('count', 10) # Lower default count since we are discrete now
    if cmd_id:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            for _ in range(count):
                s.sendto(f"{cmd_id}".encode(), DCS_INPUT_ADDR)
                socketio.sleep(0.02) # Small gap between clicks

@socketio.on('dcs_key')
def handle_dcs_key(data):
    key_name = data.get('key')
    print(f"⌨️  Server received key request: {key_name}")
    try:
        keyboard.press(key_name); time.sleep(0.1); keyboard.release(key_name)
    except Exception as e: print(f"❌ Key Emulation Error: {e}")

# --- API ROUTES ---
@app.route('/api/pois', methods=['GET'])
def get_pois():
    return jsonify(load_json_file(POIS_FILE, []))
@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({ 
        "current_profile": hud_data["current"], 
        "profiles_list": list(hud_data["profiles"].keys()), 
        "settings": get_current_settings(),
        # Add the persistent global flag here:
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
    """
    Saves the entire Missions Library (Missions, Routes, POIs) to one file.
    Accepts the full JSON object from the client and overwrites disk.
    """
    data = request.json
    
    # 1. Overwrite the file with the new Master State
    save_json_file(ROUTES_FILE, data)
    
    # 2. Broadcast to other clients (syncs tablets/other browsers)
    socketio.emit('routes_library_update', data)
    
    return jsonify({"status": "saved", "count": len(data)})

@app.route('/api/routes/<name>', methods=['DELETE'])
def delete_route(name):
    db = load_json_file(ROUTES_FILE, {})
    if name in db: 
        del db[name]
        save_json_file(ROUTES_FILE, db)
        
    # 📢 BROADCAST: Tell everyone a route is gone
    socketio.emit('routes_library_update', db)
    
    return jsonify(db)

@app.route('/api/airports', methods=['GET'])
def get_airports():
    return jsonify(load_json_file(os.path.join(DATA_DIR, 'airports.json'), {}))   

@app.route('/api/map/settings', methods=['GET'])
def get_map_settings():
    default_map = { "coords": "latlon", "altUnit": "ft", "distUnit": "nm", "defAlt": 20000, "layer": "dark", "uiScale": "1.0", "visibleRoutes": [], "vis": { "airports": True, "units": True, "alt": True, "hdg": True, "hud": False } }
    return jsonify(load_json_file(MAP_CONFIG_FILE, default_map))

@app.route('/api/map/settings', methods=['POST'])
def save_map_settings():
    global _map_settings_cache
    data = request.json
    save_json_file(MAP_CONFIG_FILE, data)
    _map_settings_cache = data
    
    # 📢 BROADCAST: Tell all connected maps to update visually
    socketio.emit('map_settings_update', data)

    # 📢 TCP PUSH: Update DCS Hook
    if tcp_client_socket:
        try:
            payload = { "type": "config", "vis": data.get("vis", {}) }
            tcp_client_socket.sendall((json.dumps(payload) + "\n").encode('utf-8'))
        except Exception as e:
            print(f"❌ TCP Push Error: {e}")
    
    return jsonify({"status": "saved", "settings": data})       
    
     #       TARGETING CYCLE
@socketio.on('activate_poi_route')
def handle_activate_poi_route(data):
    """
    Loads all Visual POIs as the active navigation route.
    Sets the active index to the specific POI requested.
    """
    global active_route_name
    target_index = data.get('index', 0)
    
    # 1. Load current POIs
    pois = load_json_file(POIS_FILE, [])
    
    if not pois:
        return
        
    # 2. Save Current Route before switching (If we want to be able to restore it later)
    # Only save if we are NOT already in Visual Mode (to avoid overwriting the backup with POIs)
    # We check if the first point of current route has type 'poi'
    is_already_visual = (len(nav.route) > 0 and nav.route[0].get('type') == 'poi')
    if not is_already_visual and len(nav.route) > 0:
        global last_standard_route_cache
        last_standard_route_cache = {"route": nav.route, "index": nav.active_wp_index}

    # 3. Convert POIs to Route format
    route_data = []
    for i, p in enumerate(pois):
        p_copy = p.copy()
        p_copy['type'] = 'poi'      # Force 'poi' type for HUD "T" display
        p_copy['name'] = f"T{i + 1}" # Force "T#" name
        route_data.append(p_copy)
        
    # 4. Update Server State
    nav.route = route_data
    nav.active_wp_index = target_index
    
    # 5. FORCE CLIENT SYNC (The Fix)
    # This tells map.html: "Drop your old route, here is the new Visual data"
    socketio.emit('force_route_sync', {
        'route': route_data, 
        'index': target_index, 
        'name': "Visual Targets"
    })
    
    socketio.emit('msg', f"Tactical Mode: T{target_index+1} Active")

def perform_nav_stop():
    """ Clears the current route on Server and Clients """
    global active_route_name # <--- Add Global
    
    nav.route = []
    nav.active_wp_index = -1
    active_route_name = None # <--- Clear Name
    
    # Tell clients to clear their lines/data
    socketio.emit('force_route_sync', {
        'route': [], 
        'index': -1, 
        'name': "Route Cleared"
    })
    socketio.emit('msg', "Navigation Stopped")
    print("🛑 HUD: Navigation Disengaged")

@socketio.on('restore_last_route')
def handle_restore_last_route():
    """ Switch back to the last standard route (Toggle Logic) """
    global last_standard_route_cache
    
    # 1. CHECK: Are we currently flying a Standard Route?
    # (Route exists AND first point is NOT a POI)
    is_running_standard = (len(nav.route) > 0 and nav.route[0].get('type') != 'poi')

    if is_running_standard:
        # TOGGLE OFF: Stop Navigation
        perform_nav_stop()
        return

    # 2. ELSE: Restore the previous route
    if not last_standard_route_cache["route"]:
        print("No previous route to restore.")
        return

    nav.route = last_standard_route_cache["route"]
    
    idx = last_standard_route_cache["index"]
    if idx >= len(nav.route): idx = 0
    
    nav.active_wp_index = idx
    
    socketio.emit('force_route_sync', {
        'route': nav.route, 
        'index': idx, 
        'name': "Restored Route"
    })
    print(f"🔄 HUD: Restored Standard Route")

@socketio.on('activate_last_poi')
def handle_activate_last_poi():
    """
    Hotkey Trigger: Loads POIs and targets the MOST RECENT one.
    (Toggle Logic: If already active, turn off)
    """
    # 1. CHECK: Are we currently flying a Visual/POI Route?
    is_running_visual = (len(nav.route) > 0 and nav.route[0].get('type') == 'poi')

    if is_running_visual:
        # TOGGLE OFF: Stop Navigation
        perform_nav_stop()
        return

    # 2. ELSE: Activate Last POI
    pois = load_json_file(POIS_FILE, [])
    if not pois:
        print("No POIs to activate")
        return
        
    last_index = len(pois) - 1
    handle_activate_poi_route({'index': last_index})
    print(f"🎯 HUD: Engaged Visual Target {last_index + 1}")
def execute_ap_pulse(start_id, stop_id, axis, duration):
    """
    Runs in a background thread.
    1. Presses Key
    2. Holds for 'duration'
    3. Releases Key
    4. Unlocks the axis so we can fire again
    """
    try:
        # Create a temporary socket for this thread
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 1. PRESS (Start)
            s.sendto(str(start_id).encode(), DCS_INPUT_ADDR)
            
            # 2. HOLD
            socketio.sleep(duration) 
            
            # 3. RELEASE (Stop)
            s.sendto(str(stop_id).encode(), DCS_INPUT_ADDR)
            
    except Exception as e:
        print(f"Pulse Error: {e}")
    finally:
        # 4. UNLOCK (Allow next pulse)
        ap_axis_locks[axis] = False

# --- ADD THIS HELPER FUNCTION ABOVE UDP_LISTENER ---
def print_debug_console(tel, steer, map_settings):
    """ Clears console and prints a static status dashboard """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # INPUTS
    print(f"================ DCS AUTOPILOT DEBUG ================")
    print(f"--- TELEMETRY (INPUTS) ---")
    print(f"RALT:  {tel.get('alt_r', 0):.1f} m   | BARO:  {tel.get('alt_baro', 0):.1f} m")
    print(f"VVI:   {tel.get('vvi', 0):.1f} m/s  | PITCH: {tel.get('pitch', 0):.1f}°")
    print(f"ROLL:  {tel.get('roll', 0):.1f}°    | SPD:   {tel.get('spd', 0):.1f} m/s")
    print(f"")

    if not steer:
        print("--- NAV COMPUTER: IDLE (No Route) ---")
        return

    # LOGIC / OUTPUTS
    dbg = steer.get('debug', {})
    mode = dbg.get('mode', 'N/A')
    
    print(f"--- NAV COMPUTER (LOGIC) ---")
    print(f"MODE:        [{mode}]")
    print(f"WP ALT (M):  {dbg.get('tgt_alt_m', 0):.1f} m  <-- CHECK THIS VALUE!")
    print(f"ALT ERROR:   {dbg.get('alt_error', 0):.1f} m  (Positive = Too Low)")
    print(f"REQ VS:      {dbg.get('req_vs', 0):.1f} m/s")
    print(f"CMD PITCH:   {dbg.get('cmd_pitch', 0):.1f}°")
    print(f"")
    
    print(f"--- OUTPUTS (CORRECTIONS) ---")
    print(f"PITCH OUT:   {steer.get('pid_pitch_out', 0):.3f}  (-1.0 to 1.0)")
    print(f"ROLL OUT:    {steer.get('pid_roll_out', 0):.3f}   (-1.0 to 1.0)")
    print(f"AP ACTIVE:   {steer.get('ap_status', False)}")
    print(f"COMMANDS:    {steer.get('ap_cmd', [])}")
    print(f"=====================================================")


def print_debug_console(tel, steer, map_settings):
    """ Clears console and prints a static status dashboard """
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # INPUTS
    print(f"================ DCS AUTOPILOT DEBUG ================")
    print(f"--- TELEMETRY (INPUTS) ---")
    print(f"RALT:  {tel.get('alt_radar', 0):.1f} m   | BARO:  {tel.get('alt_baro', 0):.1f} m")
    print(f"VVI:   {tel.get('vvi', 0):.1f} m/s  | PITCH: {tel.get('pitch', 0):.1f}°")
    print(f"ROLL:  {tel.get('roll', 0):.1f}°    | SPD:   {tel.get('spd', 0):.1f} m/s")
    print(f"")

    if not steer:
        print("--- NAV COMPUTER: IDLE (No Route) ---")
        return

    # LOGIC / OUTPUTS
    dbg = steer.get('debug', {})
    mode = dbg.get('mode', 'N/A')
    
    print(f"--- NAV COMPUTER (LOGIC) ---")
    print(f"MODE:        [{mode}]")
    print(f"WP ALT (M):  {dbg.get('tgt_alt_m', 0):.1f} m  <-- CHECK THIS VALUE!")
    print(f"ALT ERROR:   {dbg.get('alt_error', 0):.1f} m  (Positive = Too Low)")
    print(f"REQ VS:      {dbg.get('req_vs', 0):.1f} m/s")
    print(f"CMD PITCH:   {dbg.get('cmd_pitch', 0):.1f}°")
    print(f"")
    
    print(f"--- OUTPUTS (CORRECTIONS) ---")
    print(f"PITCH OUT:   {steer.get('pid_pitch_out', 0):.3f}  (-1.0 to 1.0)")
    print(f"ROLL OUT:    {steer.get('pid_roll_out', 0):.3f}   (-1.0 to 1.0)")
    print(f"AP ACTIVE:   {steer.get('ap_status', False)}")
    print(f"COMMANDS:    {steer.get('ap_cmd', [])}")
    print(f"=====================================================")

# --- UPDATED UDP LISTENER ---
def udp_listener():
    global last_known_telemetry
    global valid_look_cache
    global udp_alive
    global last_udp_time

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
                    
                    # Set UDP alive flag (triggers TCP reconnection)
                    udp_alive = True
                    last_udp_time = time.time()
                    
                    if '"type":"units"' in decoded: 
                        socketio.emit('tactical', json.loads(decoded))
                        continue
                    tel = json.loads(decoded)
                    if tel.get('type') == 'player':
                        # Look cache logic...
                        l_lat = float(tel.get('look_lat', 0))
                        l_lon = float(tel.get('look_lon', 0))
                        if l_lat != 0 and l_lon != 0:
                            valid_look_cache['lat'] = l_lat
                            valid_look_cache['lon'] = l_lon
                            valid_look_cache['alt'] = float(tel.get('look_alt', 0))
                            valid_look_cache['time'] = time.time()
                        batch_telemetry = tel 
                except BlockingIOError: 
                    break 
            
            if batch_telemetry:
                last_known_telemetry.update(batch_telemetry)
                steer = nav.calculate(batch_telemetry, _map_settings_cache)
                
                # --- DEBUG PRINT (Approx 5Hz to avoid flicker) ---
                frame_count += 1
                if frame_count % 6 == 0:
                    # print_debug_console(batch_telemetry, steer, _map_settings_cache)
                    pass

                # =========================================================
                # AUTOPILOT EXECUTION
                # =========================================================
                if steer and steer.get('ap_status', False):
                    # 1. GET PID OUTPUTS
                    roll_strength = float(steer.get('pid_roll_out', 0.0))
                    pitch_strength = float(steer.get('pid_pitch_out', 0.0))
                    
                    # 2. CALCULATE DURATION
                    calc_roll_dur = abs(roll_strength) * 0.2
                    calc_roll_dur = max(0.02, min(0.2, calc_roll_dur))

                    calc_pitch_dur = abs(pitch_strength) * 0.05 
                    calc_pitch_dur = max(0.02, min(0.1, calc_pitch_dur))

                    # 3. EXECUTE THREADS
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

                    # 4. SAFETY RESET
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

@app.route('/')
def map_page(): return render_template('map.html')
@app.route('/hud')
def hud_page(): return render_template('hud.html')
@app.route('/static/<path:filename>')
def serve_static(filename): return send_from_directory(os.path.join(app.root_path, 'static'), filename)    
def command_looper(): 
    """ Continuously fires commands that are active """
    global active_command_loops
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while True:
        try:
            if active_command_loops:
                for cmd_id in list(active_command_loops):
                    # Send Just ID
                    msg = f"{cmd_id}".encode()
                    udp_sock.sendto(msg, DCS_INPUT_ADDR)
            
            time.sleep(0.25) # 50Hz
            
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(1)

def hover_loop():
    """
    Background thread: Checks if mouse is hovering over a clickable point.
    Runs at 30Hz when enabled. Sleep mode when disabled.
    """
    print("👀 Hover Detector Started")
    
    cached_points = []
    last_cache_time = 0
    
    while True:
        try:
            # --- 1. PERFORMANCE GATE (KILL SWITCH) ---
            # If disabled, sleep long and skip ALL math. Zero CPU impact.
            if not clickable_mode_enabled:
                socketio.sleep(2) 
                continue

            # --- 2. CACHE UPDATES ---
            # Reload points every 2 seconds so you don't read disk 30 times a second
            if time.time() - last_cache_time > 2.0:
                cached_points = load_json_file(CLICKABLE_FILE, [])
                last_cache_time = time.time()

            # --- 3. VALIDATION ---
            if not last_known_telemetry or not cached_points:
                socketio.sleep(0.1)
                continue

            mouse_global = MouseTracker.get_cursor_position()
            if not mouse_global:
                socketio.sleep(0.1)
                continue

            # --- 4. GEOMETRY SETUP ---
            settings = get_current_settings()
            win_w = int(settings.get('win_w', 1920))
            win_h = int(settings.get('win_h', 1080))
            win_x = int(settings.get('win_x', 0))
            win_y = int(settings.get('win_y', 0))
            fov = float(settings.get('fov', 80.0))

            # Mouse relative to Overlay Window
            mx_local = mouse_global[0] - win_x
            my_local = mouse_global[1] - win_y

            # --- 5. RAYCASTING ---
            t = last_known_telemetry
            cam_pos = t['cam']['p']
            cam_fwd = t['cam']['x']
            
            # Use global radius with fallback, same as handle_interaction
            closest_dist = CLICK_HIT_RADIUS if 'CLICK_HIT_RADIUS' in globals() else 20
            found_pt = None

            for pt in cached_points:
                # Reconstruct World Pos
                body_offset = {'x': pt.get('x',0), 'y': pt.get('y',0), 'z': pt.get('z',0)}
                plane_hpb = {'heading': t['hdg'], 'pitch': t['pitch'], 'bank': t['roll']}
                world_pos = MathUtils.get_world_position(t['self_pos'], plane_hpb, body_offset)

                # Depth Check (Is it behind camera?)
                rel = MathUtils.vec_sub(world_pos, cam_pos)
                depth = rel['x']*cam_fwd['x'] + rel['y']*cam_fwd['y'] + rel['z']*cam_fwd['z']
                if depth <= 0: continue 

                # Project to Screen
                screen_pt = MathUtils.world_to_screen(world_pos, t['cam'], (win_w, win_h), fov)
                
                if screen_pt:
                    dist = math.hypot(screen_pt['x'] - mx_local, screen_pt['y'] - my_local)
                    if dist < closest_dist:
                        closest_dist = dist
                        found_pt = pt

            # --- 6. EMIT RESULT ---
            if found_pt:
                # Determine Label
                label = found_pt.get('name')
                if not label or label == "New Point":
                    val = found_pt.get('action_val', '')
                    label = str(val) if val else f"ID {found_pt.get('id')}"

                socketio.emit('hover_status', {
                    'active': True,
                    'x': mx_local, 
                    'y': my_local,
                    'label': label
                })
            else:
                socketio.emit('hover_status', {'active': False})

            # Run at ~30Hz
            socketio.sleep(0.016)

        except Exception as e:
            print(f"Hover Loop Error: {e}")
            socketio.sleep(1.0)


# --- TCP CONNECTOR (STRICT BLOCK 2 IMPLEMENTATION) ---
# Global flags for smart reconnection
udp_alive = False
last_udp_time = 0
UDP_TIMEOUT = 5.0  # Strict 5s timeout (User Requirement)

def tcp_connector():
    """
    Block 2: Robust Consumer Loop
    - Boot Mode: 3 attempts at 0.1Hz
    - Active Mode: 1Hz retry if UDP alive
    - Disconnect: 3-strike Zero-Byte rule or UDP Timeout
    """
    global tcp_client_socket
    global udp_alive
    global last_udp_time
    
    print(f"📡 TCP Connector: Initializing Block 2 logic...")
    
    # 1. BOOT MODE (Try to connect early)
    print("👢 TCP Boot Mode: Attempting 3 initial connections...")
    for i in range(3):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect(("127.0.0.1", TCP_PORT))
            sock.settimeout(None) # Blocking for read
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) # Low latency
            
            print(f"✅ Connected to DCS Hook (Boot Phase)")
            tcp_client_socket = sock
            handle_tcp_stream(sock) # Enter Read Loop
            break # If main loop returns, we disconnected
        except (ConnectionRefusedError, socket.timeout):
            print(f"   Boot Attempt {i+1}/3 failed (DCS not ready)")
            time.sleep(10.0) # 0.1Hz
        except Exception as e:
            print(f"   Boot Error: {e}")
            
    print("🕒 Entering Active Mode (Waiting for UDP Trigger)...")

    # 2. ACTIVE MODE (Forever Loop)
    while True:
        try:
            # Smart Reconnection: Only if UDP is flowing
            if not udp_alive:
                time.sleep(1.0)
                continue
                
            # UDP Stale Check
            if time.time() - last_udp_time > UDP_TIMEOUT:
                if udp_alive:
                    print("⏸️ UDP Flow Lost (Timeout 5s)")
                    udp_alive = False
                time.sleep(1.0)
                continue
                
            # Attempt Connection
            print("🔄 UDP Active - Connecting to Hook...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            
            try:
                sock.connect(("127.0.0.1", TCP_PORT))
                sock.settimeout(None) # Blocking
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                print(f"✅ Connected to DCS Hook (Active Phase)")
                tcp_client_socket = sock
                handle_tcp_stream(sock) # Block here until disconnect
                
            except (ConnectionRefusedError, socket.timeout):
                print("   Hook not listening... retrying in 1s")
                time.sleep(1.0) # 1Hz
                
        except Exception as e:
            print(f"❌ TCP Connector Crash: {e}")
            time.sleep(5.0)

def handle_tcp_stream(sock):
    """
    Reads from socket until disconnect.
    Implements 3-strike Zero-Byte rule.
    """
    global tcp_client_socket, last_udp_time
    buffer = ""
    zero_byte_strikes = 0
    
    try:
        while True:
            # Check for Activity Timeout during read loop
            if time.time() - last_udp_time > UDP_TIMEOUT:
               print("🛑 Disconnect: Activity Timeout (5s)")
               break
               
            try:
                data = sock.recv(4096)
                
                # Zero-Byte Detection
                if not data:
                    zero_byte_strikes += 1
                    if zero_byte_strikes >= 3:
                        print("🛑 Disconnect: 3x Zero-Byte Reads")
                        break
                    time.sleep(0.1)
                    continue
                else:
                    zero_byte_strikes = 0 # Reset on valid data
                    last_udp_time = time.time() # Reset Watchdog on TCP Data
                    
                buffer += data.decode('utf-8', errors='ignore')
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip(): continue
                    
                    try:
                        msg = json.loads(line)
                        msg_type = msg.get("type")
                        
                        if msg_type == "heartbeat":
                             # Heartbeat is silent to avoid spam
                             pass
                             
                        elif msg_type == "metadata":
                             # Phase 2a: Metadata Received
                             data = msg.get("data", {})
                             p_name = data.get("player_name", "Unknown")
                             u_name = data.get("unit_name", "Unknown")
                             print(f"👤 Metadata: Player={p_name}, Unit={u_name}")
                             socketio.emit('metadata', data) # Send to frontend
                             
                        elif msg_type == "theater_state":
                             # Phase 2b: World Objects Received
                             data = msg.get("data", {})
                             count = len(data) if data else 0
                             print(f"🎭 Objects: {count}")
                             socketio.emit('theater_state', data) # Send to frontend
                    except:
                        pass # Ignore JSON errors
                        
            except ConnectionResetError:
                print("🛑 Disconnect: Connection Reset")
                break
                
    except Exception as e:
        print(f"🛑 Disconnect Error: {e}")
        
    finally:
        sock.close()
        tcp_client_socket = None

# --- START THREADS ---
if __name__ == '__main__':
    # 1. Start Background Threads
    t_udp = threading.Thread(target=udp_listener); t_udp.daemon = True; t_udp.start()
    t_tcp = threading.Thread(target=tcp_connector); t_tcp.daemon = True; t_tcp.start() # <--- CHANGED
    t_loop = threading.Thread(target=command_looper); t_loop.daemon = True; t_loop.start()
    socketio.start_background_task(hover_loop)
    print(f"🌍 SERVER RUNNING: http://127.0.0.1:{WEB_PORT}")
    
    # 2. Launch Overlay and Track Process
    overlay_process = None
    # Check for the file inside modules/
    overlay_path = os.path.join("modules", "overlay.py")
    
    if os.path.exists(overlay_path):
        print("🚀 Launching HUD Overlay...")
        overlay_process = subprocess.Popen([sys.executable, overlay_path])
    else:
        print(f"⚠️ Warning: {overlay_path} not found.")

    # 3. Register Cleanup (Kills overlay when server stops)
    def cleanup():
        if overlay_process:
            print("🛑 Killing Overlay Process...")
            overlay_process.terminate()
            
    atexit.register(cleanup)

    # 4. Run Server
    try:
        socketio.run(app, host='0.0.0.0', port=WEB_PORT)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()