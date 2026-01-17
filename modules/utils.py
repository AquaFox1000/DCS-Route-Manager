import math

class MathUtils:
    @staticmethod
    def get_rotation_matrix(heading, pitch, bank):
        """
        Creates a 3x3 Rotation Matrix (Body -> World) for DCS.
        Sequence: Ry(Heading) * Rz(Pitch) * Rx(Bank)
        DCS Axes: X=North, Y=Up, Z=East
        """
        # 1. Inputs
        # Negate heading because DCS is Clockwise, Math is Counter-Clockwise
        h = -heading
        p = pitch
        b = bank
        
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

        # Return as Rows
        return [
            [r00, r01, r02],
            [r10, r11, r12],
            [r20, r21, r22]
        ]

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