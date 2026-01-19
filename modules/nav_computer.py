import math
import time
from modules.utils import PIDController, MathUtils

class NavComputer:
    def __init__(self):
        self.route = []
        self.active_wp_index = -1
        self.prev_wp_location = None 
        self.prev_wp_alt = None      

        self.auto_sequence = True
        self.ap_engaged = False 

        # Terrain Following State
        self.tf_state = {
            "last_rad_alt": None,
            "last_time": 0,
            "smoothed_rad_rate": 0.0
        }

        # --- TUNING ---
        self.base_roll_kp = 0.08  
        self.roll_pid = PIDController(kp=self.base_roll_kp, ki=0.005, kd=0.15, output_limits=(-1.0, 1.0))
        self.pitch_pid = PIDController(kp=0.04, ki=0.005, kd=0.1, output_limits=(-1.0, 1.0))

        # --- LIMITS ---
        self.max_pitch_cmd = 20.0 
        self.max_bank_cmd = 45.0  

    def reset_pids(self):
        self.roll_pid.reset()
        self.pitch_pid.reset()
        self.tf_state = {"last_rad_alt": None, "last_time": 0, "smoothed_rad_rate": 0.0}

    def set_route(self, route, index):
        self.route = route
        self.active_wp_index = index
        self.prev_wp_location = None 
        self.prev_wp_alt = None

    def engage_ap(self):
        if self.active_wp_index != -1 and len(self.route) > 0:
            self.ap_engaged = True
            self.reset_pids()
            return True
        return False

    def disengage_ap(self):
        self.ap_engaged = False
        self.reset_pids()

    def cycle_waypoint(self, direction):
        if not self.route: return None
        if 0 <= self.active_wp_index < len(self.route):
            curr = self.route[self.active_wp_index]
            self.prev_wp_location = (curr['lat'], curr['lon'])
            self.prev_wp_alt = float(curr.get('alt', 2000))

        self.active_wp_index = (self.active_wp_index + direction) % len(self.route)
        return self.active_wp_index

    # --- MAIN CALCULATION LOOP ---
    def calculate(self, telemetry, map_settings):
        if self.active_wp_index < 0 or self.active_wp_index >= len(self.route): 
            return None
        
        # 1. UNPACK & VALIDATE (Forward Check)
        t = self._unpack_telemetry(telemetry)
        if not t: 
            return None # Sensor Fail or Not Ready

        tgt = self.route[self.active_wp_index]

        # 2. LATERAL GUIDANCE
        lat_res = self._guidance_lateral(t, tgt, map_settings)
        
        # 3. VERTICAL GUIDANCE
        vert_res = self._guidance_vertical(t, tgt)
        
        # 4. SEQUENCING
        did_seq = self._check_sequencing(t, tgt, lat_res['dist_nm'], map_settings)

        # 5. PID CONTROL & SAFETY (Back Check)
        steer_cmd = self._calculate_steering(t, lat_res['cmd_bank'], vert_res['cmd_pitch'])

        return {
            "index": self.active_wp_index,
            "dist": lat_res['dist_nm'],
            "brg": lat_res['brg_to_tgt'],
            "turn": lat_res['hdg_err'],
            "ete": (lat_res['dist_nm'] / (t['spd'] * 0.000539957) * 3600) if t['spd'] > 1 else 0,
            "name": tgt.get('name', f'WP {self.active_wp_index+1}'),
            "lat": tgt['lat'], "lon": tgt['lon'], "alt": vert_res['display_alt_m'], 
            "type": tgt.get('type', 'wp'), "sequenced": did_seq,
            "fd_bank": lat_res['cmd_bank'] - t['roll'], 
            "fd_pitch": vert_res['cmd_pitch'] - t['pitch'],
            "req_bank": lat_res['cmd_bank'], 
            "req_pitch": vert_res['cmd_pitch'],
            "pid_roll_out": steer_cmd['roll_out'], 
            "pid_pitch_out": steer_cmd['pitch_out'],
            "ap_status": self.ap_engaged, 
            "ap_cmd": steer_cmd['ap_commands'],
            "ap_mode": lat_res['mode_str'],
            "alt_mode": vert_res['mode_str'],
            "xte": lat_res['xtk_nm'],
            "debug": {
                "mode": vert_res['mode_str'],
                "tgt_alt_m": tgt.get('alt', 0),
                "rad_alt_m": t['rad_alt'],
                "cmd_pitch": vert_res['cmd_pitch']
            }
        }

    # --- SUB-SYSTEMS ---

    def _unpack_telemetry(self, telemetry):
        try:
            # Safely cast to float. Default to 0 if missing.
            # Check for NaN/Inf (Sensor Safety)
            t = {}
            for k in ['lat', 'lon', 'hdg', 'alt_r', 'roll', 'pitch', 'spd', 'aoa', 'vvi', 'alt_baro']:
                val = float(telemetry.get(k, 0))
                if math.isnan(val) or math.isinf(val):
                    return None # Data integrity fail
                t[k] = val
            
            # Map keys to internal names
            return {
                'lat': t['lat'], 'lon': t['lon'],
                'hdg': t['hdg'], 'rad_alt': t['alt_r'],
                'roll': t['roll'], 'pitch': t['pitch'],
                'spd': t['spd'], 'aoa': t['aoa'],
                'vvi': t['vvi'], 'baro': t['alt_baro']
            }
        except Exception:
            return None

    def _guidance_lateral(self, t, tgt, map_settings):
        use_course_line = map_settings.get('navCourseLine', False)
        
        # Great Circle to Target
        dist_nm, brg_to_tgt = MathUtils.get_great_circle_data(t['lat'], t['lon'], tgt['lat'], tgt['lon'])
        
        target_bearing_cmd = brg_to_tgt 
        xtk_nm = 0.0
        mode_str = "Homing"

        if use_course_line:
            mode_str = "Course Line"
            if self.prev_wp_location:
                p_lat, p_lon = self.prev_wp_location
                xtk_nm, course_brg = MathUtils.get_cross_track_error(t['lat'], t['lon'], p_lat, p_lon, tgt['lat'], tgt['lon'])
                
                # Intercept Logic (Max 45 deg cut)
                intercept_angle = max(-45.0, min(45.0, xtk_nm * -40.0))
                target_bearing_cmd = (course_brg + intercept_angle + 360) % 360
            else:
                target_bearing_cmd = brg_to_tgt

        # Heading Error
        hdg_err = (target_bearing_cmd - t['hdg'] + 360) % 360
        if hdg_err > 180: hdg_err -= 360
        
        # Bank Command Calculation
        speed_mps = t['spd'] if t['spd'] > 10 else 10
        # Dynamic Scaling creates smoother turns at high speed
        speed_scaling = min(1.2, max(0.4, 150.0 / speed_mps))
        self.roll_pid.kp = self.base_roll_kp * speed_scaling

        base_bank = hdg_err * 2.5 
        cmd_bank = max(-self.max_bank_cmd, min(self.max_bank_cmd, base_bank))

        return {
            'dist_nm': dist_nm,
            'brg_to_tgt': brg_to_tgt,
            'hdg_err': hdg_err,
            'xtk_nm': xtk_nm,
            'cmd_bank': cmd_bank,
            'mode_str': mode_str
        }

    def _guidance_vertical(self, t, tgt):
        raw_tgt_alt_m = float(tgt.get('alt', 0))
        tgt_alt_type = tgt.get('altType', 'MSL')
        is_noe_eligible = (tgt.get('type') == 'wp') and (tgt_alt_type == 'AGL') and (raw_tgt_alt_m < 1500)
        
        cmd_pitch = 0.0
        display_alt_m = raw_tgt_alt_m
        mode_str = "BARO"
        
        min_pitch = -self.max_pitch_cmd
        max_pitch = self.max_pitch_cmd

        if is_noe_eligible:
            # === NOE MODE ===
            display_alt_m = raw_tgt_alt_m
            min_pitch = -10.0; max_pitch = 25.0

            if t['rad_alt'] < 1500:
                mode_str = "NOE_ACTIVE"
                req_vs = self._calculate_terrain_slope_cmd(raw_tgt_alt_m, t['rad_alt'], t['vvi'])
                vvi_error = req_vs - t['vvi']
                cmd_pitch = (vvi_error * 0.5) + t['aoa']
            else:
                mode_str = "NOE_SEARCH"
                target_vs = (raw_tgt_alt_m - t['baro']) * 0.5
                target_vs = max(-30.0, min(30.0, target_vs))
                cmd_pitch = ((target_vs - t['vvi']) * 0.5) + t['aoa']
        else:
            # === BARO MODE ===
            flight_alt_m = raw_tgt_alt_m
            if tgt.get('type') in ['tgt', 'poi']:
                 flight_alt_m = self.prev_wp_alt if self.prev_wp_alt is not None else t['baro']
            
            display_alt_m = flight_alt_m
            alt_error = flight_alt_m - t['baro']
            
            # Dampening
            damped_vvi = 0.0
            if abs(t['vvi']) > 1.0:
                sign = 1.0 if t['vvi'] > 0 else -1.0
                damped_vvi = (abs(t['vvi']) - 1.0) * sign
            
            effective_error = alt_error - (damped_vvi * 5.0)
            if abs(effective_error) < 5.0: effective_error = 0.0

            target_vs = max(-90.0, min(90.0, effective_error * 0.5))
            cmd_pitch = ((target_vs - t['vvi']) * 0.5) + t['aoa']

        # Stall Protection / Energy Recovery Logic
        spd_kmh = t['spd'] * 3.6
        if self.ap_engaged:
            if spd_kmh < 300: # Energy Recovery
                cmd_pitch = -5.0 # Nose down
                mode_str = "STALL_RECOVERY"
            elif spd_kmh < 350 and cmd_pitch > 0: # Authority Limiter
                 ratio = (spd_kmh - 300) / 50.0
                 cmd_pitch = cmd_pitch * ratio

        # Final Clamp
        cmd_pitch = max(min_pitch, min(max_pitch, cmd_pitch))

        return {
            'cmd_pitch': cmd_pitch,
            'display_alt_m': display_alt_m,
            'mode_str': mode_str
        }

    def _check_sequencing(self, t, tgt, dist_nm, map_settings):
        if not self.auto_sequence: return False
        
        should_seq = False
        use_course_line = map_settings.get('navCourseLine', False)
        
        if tgt.get('type') in ['tgt', 'poi']:
            # Fly-over Logic (Dot Product)
            # Todo: use MathUtils here too for consistency if needed
            # For now, simple lat/lon logic is fine for short range sequencing
            d_lat_t = tgt['lat'] - t['lat']
            d_lon_t = tgt['lon'] - t['lon']
            
            if self.prev_wp_location:
                 track_lat = tgt['lat'] - self.prev_wp_location[0]
                 track_lon = tgt['lon'] - self.prev_wp_location[1]
            else:
                 rad_hdg = math.radians(t['hdg'])
                 track_lat = math.cos(rad_hdg)
                 track_lon = math.sin(rad_hdg)
            
            dot_prod = (d_lat_t * track_lat) + (d_lon_t * track_lon)
            if dot_prod <= 0: should_seq = True
        else:
            # Radius Logic
            tol = 0.5 if use_course_line else 0.27
            if dist_nm < tol: should_seq = True

        if should_seq:
            self.cycle_waypoint(1)
            return True
        return False

    def _calculate_steering(self, t, cmd_bank, cmd_pitch):
        ap_commands = []
        
        # 1. PID Update
        roll_out = self.roll_pid.update(cmd_bank - t['roll'])
        pitch_out = self.pitch_pid.update(cmd_pitch - t['pitch'])

        # 2. Output Validation (Safety Back Track)
        if math.isnan(roll_out) or math.isnan(pitch_out) or math.isinf(roll_out) or math.isinf(pitch_out):
            self.disengage_ap()
            return {'roll_out': 0, 'pitch_out': 0, 'ap_commands': ["SAFETY_RESET"]}

        # 3. Disengage Checks
        if self.ap_engaged:
            # Extreme Attitude Check
            if abs(t['roll']) > 60 or abs(t['pitch']) > 35:
                self.disengage_ap()
                ap_commands.append("SAFETY_RESET")
            
            # Speed Check
            elif (t['spd'] * 3.6) < 260:
                self.disengage_ap()
                ap_commands.append("STALL_DISENGAGE")
            
            else:
                # Generate Stick Commands
                if abs(roll_out) > 0.05:
                    ap_commands.append("ROLL_RIGHT" if roll_out > 0 else "ROLL_LEFT")
                if abs(pitch_out) > 0.05:
                    ap_commands.append("PITCH_UP" if pitch_out > 0 else "PITCH_DOWN")

        return {
            'roll_out': roll_out,
            'pitch_out': pitch_out,
            'ap_commands': ap_commands
        }

    def _calculate_terrain_slope_cmd(self, target_agl_m, current_rad_alt_m, plane_vvi_ms):
        ALPHA = 0.15      
        KP = 1.0          
        DEADZONE = 5.0    
        MAX_SINK = -7.5   
        
        now = time.time()
        dt = now - self.tf_state["last_time"]
        
        if self.tf_state["last_rad_alt"] is None or dt > 0.5 or dt <= 0:
            self.tf_state["last_rad_alt"] = current_rad_alt_m
            self.tf_state["last_time"] = now
            self.tf_state["smoothed_rad_rate"] = 0.0
            return 0.0

        raw_rate = (current_rad_alt_m - self.tf_state["last_rad_alt"]) / dt
        ema = self.tf_state["smoothed_rad_rate"]
        smoothed_rate = (ALPHA * raw_rate) + ((1 - ALPHA) * ema)
        self.tf_state["smoothed_rad_rate"] = smoothed_rate
        
        self.tf_state["last_rad_alt"] = current_rad_alt_m
        self.tf_state["last_time"] = now

        terrain_slope = plane_vvi_ms - smoothed_rate
        error = target_agl_m - current_rad_alt_m
        
        err_corr = 0.0
        if abs(error) > DEADZONE:
            sign = 1 if error > 0 else -1
            err_corr = (abs(error) - DEADZONE) * sign * KP

        cmd_vs = terrain_slope + err_corr

        if error > 0: cmd_vs = max(0.0, cmd_vs)
        else: cmd_vs = max(MAX_SINK, cmd_vs)

        return cmd_vs