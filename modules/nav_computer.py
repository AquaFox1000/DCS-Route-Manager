# nav_computer.py
import math
import time 

class PIDController:
    def __init__(self, kp, ki, kd, output_limits=(-1.0, 1.0), integral_limit=1.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_out, self.max_out = output_limits
        self.integral_limit = integral_limit
        
        self._integral = 0.0
        self._prev_error = 0.0
        self._last_time = time.time()
        
    def reset(self):
        self._integral = 0.0
        self._prev_error = 0.0
        self._last_time = time.time()
        
    def update(self, error, dt=None):
        current_time = time.time()
        if dt is None:
            dt = current_time - self._last_time
            if dt <= 0: dt = 0.02
        self._last_time = current_time

        # Proportional
        p_out = self.kp * error
        
        # Integral
        self._integral += error * dt
        self._integral = max(-self.integral_limit, min(self.integral_limit, self._integral))
        i_out = self.ki * self._integral
        
        # Derivative
        derivative = (error - self._prev_error) / dt
        d_out = self.kd * derivative
        
        self._prev_error = error
        
        output = p_out + i_out + d_out
        return max(self.min_out, min(self.max_out, output))

class NavComputer:
    def __init__(self):
        self.route = []
        self.active_wp_index = -1
        self.prev_wp_location = None 
        self.prev_wp_alt = None      

        self.auto_sequence = True
        self.ap_engaged = False 

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
        self.alt_gain_p = 0.15 

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

    def get_great_circle_data(self, lat1, lon1, lat2, lon2):
        R = 3440.065 
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist = R * c
        
        y = math.sin(dlon) * math.cos(math.radians(lat2))
        x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon)
        brg = (math.degrees(math.atan2(y, x)) + 360) % 360
        return dist, brg

    def get_cross_track_error(self, my_lat, my_lon, start_lat, start_lon, end_lat, end_lon):
        dist_total, course_brg = self.get_great_circle_data(start_lat, start_lon, end_lat, end_lon)
        dist_to_plane, brg_to_plane = self.get_great_circle_data(start_lat, start_lon, my_lat, my_lon)
        angle_diff = math.radians(brg_to_plane - course_brg)
        xtk_nm = math.asin(math.sin(dist_to_plane / 3440.065) * math.sin(angle_diff)) * 3440.065
        return xtk_nm, course_brg

    def calculate_terrain_slope_cmd(self, target_agl_m, current_rad_alt_m, plane_vvi_ms):
        """ NOE Logic: Returns Commanded VS based on Terrain Slope """
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

        if error > 0: 
            cmd_vs = max(0.0, cmd_vs)
        else:
            cmd_vs = max(MAX_SINK, cmd_vs)

        return cmd_vs

    def calculate(self, telemetry, map_settings):
        if self.active_wp_index < 0 or self.active_wp_index >= len(self.route): 
            return None
        
        # 1. TELEMETRY
        my_lat = float(telemetry.get('lat', 0))
        my_lon = float(telemetry.get('lon', 0))
        my_hdg = float(telemetry.get('hdg', 0))
        my_rad_alt = float(telemetry.get('alt_r', 10000)) # FIXED: 'alt_r'
        my_roll = float(telemetry.get('roll', 0))
        my_pitch = float(telemetry.get('pitch', 0))
        my_spd = float(telemetry.get('spd', 1)) 
        my_aoa = float(telemetry.get('aoa', 0))
        my_vvi = float(telemetry.get('vvi', 0))
        my_baro = float(telemetry.get('alt_baro', 0))

        tgt = self.route[self.active_wp_index]
        tgt_type = tgt.get('type', 'wp')
        use_course_line = map_settings.get('navCourseLine', False)

        # 2. LATERAL
        dist_nm, brg_to_tgt = self.get_great_circle_data(my_lat, my_lon, tgt['lat'], tgt['lon'])
        target_bearing_cmd = brg_to_tgt 
        xtk_nm = 0.0

        if use_course_line:
            if self.prev_wp_location:
                p_lat, p_lon = self.prev_wp_location
                xtk_nm, course_brg = self.get_cross_track_error(my_lat, my_lon, p_lat, p_lon, tgt['lat'], tgt['lon'])
                intercept_angle = max(-45.0, min(45.0, xtk_nm * -40.0))
                target_bearing_cmd = (course_brg + intercept_angle + 360) % 360
            else:
                target_bearing_cmd = brg_to_tgt

        # 3. SEQUENCING
        did_seq = False
        if self.auto_sequence:
            should_seq = False
            if tgt_type in ['tgt', 'poi']:
                d_lat_t = tgt['lat'] - my_lat
                d_lon_t = tgt['lon'] - my_lon
                if self.prev_wp_location:
                    track_lat = tgt['lat'] - self.prev_wp_location[0]
                    track_lon = tgt['lon'] - self.prev_wp_location[1]
                else:
                    rad_hdg = math.radians(my_hdg)
                    track_lat = math.cos(rad_hdg)
                    track_lon = math.sin(rad_hdg)
                mag = math.hypot(track_lat, track_lon)
                if mag > 0:
                    track_lat /= mag
                    track_lon /= mag
                dot_prod = (d_lat_t * track_lat) + (d_lon_t * track_lon)
                if dot_prod <= 0: should_seq = True
            else:
                tol = 0.5 if use_course_line else 0.27
                if dist_nm < tol: should_seq = True

            if should_seq:
                self.cycle_waypoint(1)
                did_seq = True
                tgt = self.route[self.active_wp_index]
                tgt_type = tgt.get('type', 'wp')
                dist_nm, brg_to_tgt = self.get_great_circle_data(my_lat, my_lon, tgt['lat'], tgt['lon'])
                target_bearing_cmd = brg_to_tgt

        # 4. ALTITUDE & VERTICAL CONTROL
        raw_tgt_alt_m = float(tgt.get('alt', 0))
        tgt_alt_type = tgt.get('altType', 'MSL')
        
        is_noe_eligible = (tgt_type == 'wp') and (tgt_alt_type == 'AGL') and (raw_tgt_alt_m < 1500)
        
        cmd_pitch = 0.0
        display_alt_m = 0.0
        
        # Pitch Safety Limits
        min_pitch_limit = -self.max_pitch_cmd
        max_pitch_limit = self.max_pitch_cmd

        # Debug Vars
        dbg_mode = "BARO"
        dbg_req_vs = 0.0
        dbg_alt_error = 0.0

        if is_noe_eligible:
            # === NOE / TERRAIN FOLLOWING MODE ===
            target_agl_m = raw_tgt_alt_m
            display_alt_m = target_agl_m
            
            # Asymmetric Clamping for NOE
            min_pitch_limit = -10.0
            max_pitch_limit = 25.0

            if my_rad_alt < 1500:
                # [A] ACTIVE NOE (Radar Valid)
                dbg_mode = "NOE_ACTIVE"
                req_vs = self.calculate_terrain_slope_cmd(target_agl_m, my_rad_alt, my_vvi)
                
                vvi_error = req_vs - my_vvi
                cmd_pitch = (vvi_error * 0.5) + my_aoa
                
                dbg_req_vs = req_vs
                dbg_alt_error = target_agl_m - my_rad_alt
            
            else:
                # [B] SEARCH MODE (Radar Invalid)
                # Use Barometric Fallback, but enforce NOE Pitch limits (-10 to +25)
                dbg_mode = "NOE_SEARCH"
                self.tf_state["smoothed_rad_rate"] = 0.0 
                
                # --- VELOCITY CASCADE FOR SEARCH ---
                # 1. Calculate Target VS based on Distance
                alt_error = raw_tgt_alt_m - my_baro
                target_vs = alt_error * 0.5
                
                # 2. Clamp Target VS (Prevent Deep Dives > 30m/s)
                target_vs = max(-30.0, min(30.0, target_vs))
                
                # 3. Calculate VVI Error and Pitch
                vvi_error = target_vs - my_vvi
                cmd_pitch = (vvi_error * 0.5) + my_aoa
                
                dbg_alt_error = alt_error
                dbg_req_vs = target_vs

        else:
            # === STANDARD BAROMETRIC MODE ===
            dbg_mode = "BARO"
            self.tf_state = {"last_rad_alt": None, "last_time": 0, "smoothed_rad_rate": 0.0}
            
            flight_alt_m = raw_tgt_alt_m 
            if tgt_type in ['tgt', 'poi']:
                if self.prev_wp_alt is not None: flight_alt_m = self.prev_wp_alt
                else: flight_alt_m = my_baro 

            display_alt_m = flight_alt_m
            alt_error = flight_alt_m - my_baro
            
            # --- ANTICIPATION & VELOCITY LOGIC ---
            # 1. Soft Deadzone on VVI (Dampening)
            # We ignore the first 1.0 m/s of VVI to prevent wobble.
            # By subtracting 1.0 from the magnitude, we ensure there is no "jump"
            # when it kicks in (it starts at 0.0 and ramps up).
            damped_vvi = 0.0
            if abs(my_vvi) > 1.0:
                sign = 1.0 if my_vvi > 0 else -1.0
                damped_vvi = (abs(my_vvi) - 1.0) * sign
            
            # 2. Calculate Effective Error (PD Control)
            # We "look ahead" by 5.0 factor. If diving, this reduces the error 
            # early, tricking the AP into leveling off gently.
            effective_error = alt_error - (damped_vvi * 5.0)

            # 3. Altitude Deadzone (Silence the stick when close)
            if abs(effective_error) < 5.0: effective_error = 0.0

            # 4. Desired Vertical Speed (The "Pull Amount")
            # We use your requested low gain (0.5) for a gentle capture.
            target_vs = effective_error * 0.5
            
            # 5. Safety Limits & Output
            target_vs = max(-90.0, min(90.0, target_vs)) 
            cmd_pitch = ((target_vs - my_vvi) * 0.5) + my_aoa
            
            dbg_alt_error = alt_error
            dbg_req_vs = target_vs

        # Final Pitch Clamp
        cmd_pitch = max(min_pitch_limit, min(max_pitch_limit, cmd_pitch))

        spd_kmh = my_spd * 3.6
        ap_commands = [] # Ensure this list exists for later usage

        if self.ap_engaged:
            # 1. DISENGAGE (< 260 km/h)
            if spd_kmh < 260:
                self.ap_engaged = False
                ap_commands.append("STALL_DISENGAGE")
            
            # 2. ENERGY RECOVERY (< 300 km/h)
            elif spd_kmh < 300:
                # Force nose down to regain energy
                cmd_pitch = -5.0 
                dbg_mode = "STALL_RECOVERY"

            # 3. LINEAR AUTHORITY LIMIT (300 - 350 km/h)
            elif spd_kmh < 350:
                # If we are pitching UP, limit the authority to prevent stall
                # 300km/h = 0% authority, 350km/h = 100% authority
                if cmd_pitch > 0:
                    ratio = (spd_kmh - 300) / 50.0
                    cmd_pitch = cmd_pitch * ratio

        # 6. BANK CONTROL
        hdg_err = (target_bearing_cmd - my_hdg + 360) % 360
        if hdg_err > 180: hdg_err -= 360
        
        speed_mps = my_spd if my_spd > 10 else 10
        speed_scaling = min(1.2, max(0.4, 150.0 / speed_mps))
        
        base_bank = hdg_err * 2.5 
        cmd_bank = max(-self.max_bank_cmd, min(self.max_bank_cmd, base_bank))
        
        self.roll_pid.kp = self.base_roll_kp * speed_scaling

        # 7. PID EXECUTION
        roll_out = 0.0
        pitch_out = 0.0
        ap_commands = []

        if self.ap_engaged:
            roll_err = cmd_bank - my_roll
            roll_out = self.roll_pid.update(roll_err)
            
            pitch_err = cmd_pitch - my_pitch
            pitch_out = self.pitch_pid.update(pitch_err)

            if abs(my_roll) > 60 or abs(my_pitch) > 35:
                self.ap_engaged = False
                ap_commands.append("SAFETY_RESET")
            else:
                if abs(roll_out) > 0.05:
                    ap_commands.append("ROLL_RIGHT" if roll_out > 0 else "ROLL_LEFT")
                if abs(pitch_out) > 0.05:
                    ap_commands.append("PITCH_UP" if pitch_out > 0 else "PITCH_DOWN")

        return {
            "index": self.active_wp_index,
            "dist": dist_nm,
            "brg": brg_to_tgt,
            "turn": hdg_err,
            "ete": (dist_nm / (my_spd * 0.000539957) * 3600) if my_spd > 1 else 0,
            "name": tgt.get('name', f'WP {self.active_wp_index+1}'),
            "lat": tgt['lat'], "lon": tgt['lon'], "alt": display_alt_m, 
            "type": tgt_type, "sequenced": did_seq,
            "fd_bank": cmd_bank - my_roll, "fd_pitch": cmd_pitch - my_pitch,
            "req_bank": cmd_bank, "req_pitch": cmd_pitch,
            "pid_roll_out": roll_out, "pid_pitch_out": pitch_out,
            "ap_status": self.ap_engaged, "ap_cmd": ap_commands,
            "ap_mode": "Course Line" if use_course_line else "Homing",
            "alt_mode": dbg_mode,
            "xte": xtk_nm,
            "debug": {
                "mode": dbg_mode,
                "tgt_alt_m": raw_tgt_alt_m,
                "rad_alt_m": my_rad_alt,
                "alt_error": dbg_alt_error,
                "req_vs": dbg_req_vs,
                "cmd_pitch": cmd_pitch
            }
        }