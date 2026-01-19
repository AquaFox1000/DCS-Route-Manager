import math
import time

# --- SAFETY WRAPPERS ---
def safe_sqrt(val):
    if val < 0: return 0.0
    return math.sqrt(val)

def safe_asin(val):
    if val < -1.0: return -1.570796 # -PI/2
    if val > 1.0: return 1.570796  # PI/2
    return math.asin(val)

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

        # 1. Proportional
        p_out = self.kp * error
        
        # 2. Integral
        self._integral += error * dt
        self._integral = max(-self.integral_limit, min(self.integral_limit, self._integral))
        i_out = self.ki * self._integral
        
        # 3. Derivative
        derivative = (error - self._prev_error) / dt
        d_out = self.kd * derivative
        
        self._prev_error = error
        
        output = p_out + i_out + d_out
        
        # 4. Safety Clamp (Output)
        if math.isnan(output) or math.isinf(output):
            return 0.0 # Fail Safe
            
        return max(self.min_out, min(self.max_out, output))

class MathUtils:
    @staticmethod
    def get_rotation_matrix(heading_deg, pitch_deg, bank_deg):
        """
        Creates a 3x3 Rotation Matrix (Body -> World) for DCS.
        Input: Degrees (Standard DCS Telemetry)
        Sequence: Ry(Heading) * Rz(Pitch) * Rx(Bank)
        DCS Axes: X=North, Y=Up, Z=East
        """
        # 1. Convert to Radians (Fixing Bug: math.cos expects rads)
        # Negate heading because DCS is Clockwise, Math is Counter-Clockwise
        h = math.radians(-heading_deg)
        p = math.radians(pitch_deg)
        b = math.radians(bank_deg)
        
        ch, sh = math.cos(h), math.sin(h)
        cp, sp = math.cos(p), math.sin(p)
        cb, sb = math.cos(b), math.sin(b)

        # 2. Matrix Elements
        # Calculated as: Ry(h) * Rz(p) * Rx(b)
        
        # Row 0 (X-Axis World Components - North)
        r00 = ch * cp
        r01 = sh * sb - ch * sp * cb
        r02 = sh * cb + ch * sp * sb

        # Row 1 (Y-Axis World Components - Up)
        r10 = sp
        r11 = cp * cb
        r12 = -cp * sb

        # Row 2 (Z-Axis World Components - East)
        r20 = -sh * cp
        r21 = ch * sb + sh * sp * cb
        r22 = ch * cb - sh * sp * sb

        return [
            [r00, r01, r02],
            [r10, r11, r12],
            [r20, r21, r22]
        ]

    # --- GEODESIC MATH (Moved from NavComputer) ---
    @staticmethod
    def get_great_circle_data(lat1_deg, lon1_deg, lat2_deg, lon2_deg):
        R = 3440.065 # Earth Radius in NM
        
        lat1 = math.radians(lat1_deg)
        lon1 = math.radians(lon1_deg)
        lat2 = math.radians(lat2_deg)
        lon2 = math.radians(lon2_deg)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine Distance
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(safe_sqrt(a), safe_sqrt(1-a))
        dist_nm = R * c
        
        # Initial Bearing
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        brg = (math.degrees(math.atan2(y, x)) + 360) % 360
        
        return dist_nm, brg

    @staticmethod
    def get_cross_track_error(my_lat, my_lon, start_lat, start_lon, end_lat, end_lon):
        dist_total, course_brg = MathUtils.get_great_circle_data(start_lat, start_lon, end_lat, end_lon)
        dist_to_plane, brg_to_plane = MathUtils.get_great_circle_data(start_lat, start_lon, my_lat, my_lon)
        
        angle_diff = math.radians(brg_to_plane - course_brg)
        
        # Cross Track Distance (NM)
        # xtk = asin(sin(dist/R) * sin(angle)) * R
        # R = 3440.065
        R = 3440.065
        xtk_nm = safe_asin(math.sin(dist_to_plane / R) * math.sin(angle_diff)) * R
        
        return xtk_nm, course_brg

    # --- VECTOR HELPERS ---
    @staticmethod
    def vec_sub(v1, v2):
        return {'x': v1['x'] - v2['x'], 'y': v1['y'] - v2['y'], 'z': v1['z'] - v2['z']}

    @staticmethod
    def vec_add(v1, v2):
        return {'x': v1['x'] + v2['x'], 'y': v1['y'] + v2['y'], 'z': v1['z'] + v2['z']}

    @staticmethod
    def vec_scale(v, scalar):
        return {'x': v['x'] * scalar, 'y': v['y'] * scalar, 'z': v['z'] * scalar}

    @staticmethod
    def mat_mul_vec(m, v):
        """ Matrix * Vector """
        return {
            'x': m[0][0] * v['x'] + m[0][1] * v['y'] + m[0][2] * v['z'],
            'y': m[1][0] * v['x'] + m[1][1] * v['y'] + m[1][2] * v['z'],
            'z': m[2][0] * v['x'] + m[2][1] * v['y'] + m[2][2] * v['z']
        }

    @staticmethod
    def mat_transpose_mul_vec(m, v):
        """ Transpose(Matrix) * Vector (Inverse Rotation) """
        return {
            'x': m[0][0] * v['x'] + m[1][0] * v['y'] + m[2][0] * v['z'],
            'y': m[0][1] * v['x'] + m[1][1] * v['y'] + m[2][1] * v['z'],
            'z': m[0][2] * v['x'] + m[1][2] * v['y'] + m[2][2] * v['z']
        }

    @staticmethod
    def calculate_body_relative_point(plane_pos, plane_hpb, cam_pos, cam_fwd, click_dist_cm):
        dist_m = click_dist_cm / 100.0
        
        # World Interaction Point
        fwd_scaled = MathUtils.vec_scale(cam_fwd, dist_m)
        interaction_world = MathUtils.vec_add(cam_pos, fwd_scaled)
        
        # Vector from Plane Center to Point
        diff_vector = MathUtils.vec_sub(interaction_world, plane_pos)

        h = plane_hpb.get('hdg', plane_hpb.get('heading', 0))
        p = plane_hpb.get('pitch', 0)
        b = plane_hpb.get('roll', plane_hpb.get('bank', 0))

        # FIX: pass degrees directly, now handled by new method
        rot_matrix = MathUtils.get_rotation_matrix(h, p, b)
        
        # Rotate to Body Frame
        return MathUtils.mat_transpose_mul_vec(rot_matrix, diff_vector)

    @staticmethod
    def get_world_position(plane_pos, plane_hpb, body_offset):
        h = plane_hpb.get('hdg', plane_hpb.get('heading', 0))
        p = plane_hpb.get('pitch', 0)
        b = plane_hpb.get('roll', plane_hpb.get('bank', 0))

        rot_matrix = MathUtils.get_rotation_matrix(h, p, b)
        rotated_offset = MathUtils.mat_mul_vec(rot_matrix, body_offset)
        return MathUtils.vec_add(plane_pos, rotated_offset)

    @staticmethod
    def world_to_screen(target_pos, cam_matrix, screen_res, fov_horiz_deg):
        w, h = screen_res
        
        # Transform to Camera Local Space
        rel = MathUtils.vec_sub(target_pos, cam_matrix['p'])
        
        # Dot products with Camera Basis Vectors
        local_x = rel['x'] * cam_matrix['x']['x'] + rel['y'] * cam_matrix['x']['y'] + rel['z'] * cam_matrix['x']['z']
        local_y = rel['x'] * cam_matrix['y']['x'] + rel['y'] * cam_matrix['y']['y'] + rel['z'] * cam_matrix['y']['z']
        local_z = rel['x'] * cam_matrix['z']['x'] + rel['y'] * cam_matrix['z']['y'] + rel['z'] * cam_matrix['z']['z']

        if local_x <= 0: return None

        fov_rad = math.radians(fov_horiz_deg)
        tan_half_fov = math.tan(fov_rad / 2)
        aspect = w / h
        tan_half_vfov = tan_half_fov / aspect
        
        norm_x = local_z / local_x
        norm_y = local_y / local_x
        
        screen_x = (0.5 + 0.5 * (norm_x / tan_half_fov)) * w
        screen_y = (0.5 - 0.5 * (norm_y / tan_half_vfov)) * h

        return {'x': screen_x, 'y': screen_y}

    @staticmethod
    def get_next_id(points_list):
        existing_ids = {p.get('id', 0) for p in points_list}
        i = 1
        while True:
            if i not in existing_ids: return i
            i += 1