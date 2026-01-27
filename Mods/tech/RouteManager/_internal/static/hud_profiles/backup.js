        if (N.hasRoute) {

            ctx.save();

            ctx.translate(0, CENTER_Y);



            // Get Commanded Pitch/Bank from server

            let cmdPitch = N.req_pitch || 0;

            let cmdBank  = N.req_bank || 0;



            // Calculate Error (Command - Actual)

            let pitchErr = cmdPitch - T.pitch;

            let bankErr  = cmdBank  - T.roll;



            // Visual Scaling

            // Pitch: 18 px/deg (Same as ladder)

            let yDir = -pitchErr * 18;

           

            // Roll: 10 px/deg

            let xDir = bankErr * 18;



            // Visual Clamping (The Box)

            const MAX_PITCH_PX = 20 * 18; // 20 deg Up/Down

            const MAX_ROLL_DEG = 18;     // 18 deg Left/Right

            const MAX_ROLL_PX = MAX_ROLL_DEG * 18;



            if (yDir > MAX_PITCH_PX) yDir = MAX_PITCH_PX;

            if (yDir < -MAX_PITCH_PX) yDir = -MAX_PITCH_PX;

           

            if (xDir > MAX_ROLL_PX) xDir = MAX_ROLL_PX;

            if (xDir < -MAX_ROLL_PX) xDir = -MAX_ROLL_PX;



            // Draw Circle

            ctx.beginPath();

            ctx.lineWidth = 5;

            ctx.strokeStyle = data.settings.color || C.color;

            ctx.arc(xDir, yDir, 50, 0, 2 * Math.PI);

            ctx.stroke();



            ctx.restore();

        }

        class NavComputer:
    def __init__(self):
        self.route = []; self.active_wp_index = -1; self.auto_sequence = True

    def toggle_sequencing(self, state): self.auto_sequence = state

    # 1. INFINITE LOOP: MANUAL CYCLE
    def cycle_waypoint(self, direction):
        if not self.route: return None
        
        # Use Modulo (%) operator to wrap around
        # (Current + 1) % Length -> Wraps to 0 if at end
        # (Current - 1) % Length -> Wraps to Last if at 0
        self.active_wp_index = (self.active_wp_index + direction) % len(self.route)
        
        return self.active_wp_index

    def calculate(self, my_lat, my_lon, my_hdg, my_spd_ms, my_ias_ms, my_vvi_ms, my_alt_m, my_roll=0, my_pitch=0, my_aoa=0, stall_warn=0):
        if self.active_wp_index < 0 or self.active_wp_index >= len(self.route): return None
        tgt = self.route[self.active_wp_index]
        
        # --- Standard Navigation Math ---
        R = 3440.065
        dlat = math.radians(tgt['lat'] - my_lat); dlon = math.radians(tgt['lon'] - my_lon)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(my_lat)) * math.cos(math.radians(tgt['lat'])) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist_nm = R * c
        
        # Speeds
        gs_kts = my_spd_ms * 1.94384
        if gs_kts < 1: gs_kts = 1
        ete_sec = (dist_nm / gs_kts) * 3600
        ias_kmh = my_ias_ms * 3.6 

        # Altitude Correction
        raw_alt = float(tgt.get('alt', 0))
        final_alt_m = raw_alt * 0.3048 if _map_settings_cache.get('altUnit') == 'ft' else raw_alt

        # Bearing Calc
        y = math.sin(dlon) * math.cos(math.radians(tgt['lat']))
        x = math.cos(math.radians(my_lat)) * math.sin(math.radians(tgt['lat'])) - math.sin(math.radians(my_lat)) * math.cos(math.radians(tgt['lat'])) * math.cos(dlon)
        brg = (math.degrees(math.atan2(y, x)) + 360) % 360
        
        # Fail-Safe Delta
        clean_hdg = (my_hdg + 360) % 360
        clean_brg = (brg + 360) % 360
        diff = clean_brg - clean_hdg
        if diff < -180: diff += 360
        if diff > 180: diff -= 360
        cmd_turn = diff

        # --- FLIGHT DIRECTOR LOGIC (Same as before) ---
        ABS_MAX_BANK = 45
        current_max_bank = ABS_MAX_BANK
        if ias_kmh < 300:
            ratio = (ias_kmh - 200) / (300 - 200); ratio = max(0, min(1, ratio)) 
            current_max_bank = 15 + (ratio * (ABS_MAX_BANK - 15))

        SOFTNESS_EXPONENT = 1.4; START_SOFTENING_DEG = 30.0; err_mag = abs(cmd_turn); bank_demand = 0
        if err_mag >= START_SOFTENING_DEG: bank_demand = current_max_bank
        else: ratio = err_mag / START_SOFTENING_DEG; bank_demand = current_max_bank * math.pow(ratio, SOFTNESS_EXPONENT)
        req_bank = math.copysign(bank_demand, cmd_turn)

        is_gross_turn = (err_mag >= START_SOFTENING_DEG)
        if is_gross_turn:
            if (math.copysign(1, my_roll) == math.copysign(1, req_bank)) and (abs(my_roll) > abs(req_bank)): req_bank = my_roll

        req_pitch = 0; is_target = (tgt.get('type') == 'tgt')
        if is_target: req_pitch = my_aoa - (my_vvi_ms * 0.5)
        else: alt_diff = final_alt_m - my_alt_m; req_pitch = alt_diff * 0.1
        
        pitch_ceil = 20
        if ias_kmh > 350: pitch_ceil = 20
        elif ias_kmh > 310: pitch_ceil = 10 + (ias_kmh - 310)/(350-310)*(20-10)
        elif ias_kmh > 290: pitch_ceil = 0 + (ias_kmh - 290)/(310-290)*(10-0)
        elif ias_kmh > 280: pitch_ceil = -5 + (ias_kmh - 280)/(290-280)*(0 - -5)
        else: pitch_ceil = -10
        if req_pitch > pitch_ceil: req_pitch = pitch_ceil
        if req_pitch < -20: req_pitch = -20
        MAX_SAFE_AOA = 15
        if stall_warn == 1 or my_aoa > MAX_SAFE_AOA: req_pitch = -10

        # --- 2. INFINITE LOOP: NEXT WP LOOKAHEAD ---
        next_course_diff = 0
        if len(self.route) > 1:
            # Look at the NEXT index, wrapping to 0 if we are at the end
            next_idx = (self.active_wp_index + 1) % len(self.route)
            next_wp = self.route[next_idx]
            
            dlon_n = math.radians(next_wp['lon'] - tgt['lon'])
            y_n = math.sin(dlon_n) * math.cos(math.radians(next_wp['lat']))
            x_n = math.cos(math.radians(tgt['lat'])) * math.sin(math.radians(next_wp['lat'])) - math.sin(math.radians(tgt['lat'])) * math.cos(dlon_n)
            next_brg = (math.degrees(math.atan2(y_n, x_n)) + 360) % 360
            next_course_diff = next_brg - brg
            if next_course_diff < -180: next_course_diff += 360
            if next_course_diff > 180: next_course_diff -= 360

        # --- 3. INFINITE LOOP: AUTO SEQUENCE ---
        seq_dist = AUTO_SEQ_DIST_NM 
        if _map_settings_cache.get('navFlyBy', False):
            turn_rad_nm = (gs_kts ** 2) / 250000.0
            seq_dist = max(AUTO_SEQ_DIST_NM, min(turn_rad_nm, 3.0))

        did_seq = False
        if self.auto_sequence and dist_nm <= seq_dist:
             # Just increment and Modulo. 
             # If Index was 4 and Len is 5 -> (4+1)%5 = 0.
             self.active_wp_index = (self.active_wp_index + 1) % len(self.route)
             did_seq = True
             
             # Recursively calculate for the NEW waypoint immediately
             return self.calculate(my_lat, my_lon, my_hdg, my_spd_ms, my_ias_ms, my_vvi_ms, my_alt_m, my_roll, my_pitch, my_aoa, stall_warn)

        return { 
            "index": self.active_wp_index, 
            "dist": dist_nm, "brg": brg, "turn": cmd_turn, "ete": ete_sec, 
            "name": tgt.get('name', f'WP {self.active_wp_index+1}'), 
            "alt": final_alt_m, 
            "type": tgt.get('type', 'wp'), 
            "next_turn": next_course_diff, 
            "sequenced": did_seq,
            "spd": float(tgt.get('spd', 0)),
            "req_pitch": req_pitch,
            "req_bank": req_bank,
            "lat": tgt['lat'],
            "lon": tgt['lon']
        }

nav = NavComputer()