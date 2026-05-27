import numpy as np
from app.utils.geometry import distance, angle, line_angle

class PostureAnalysis:
    def __init__(self):
        # 头部
        self.NOSE = 0
        self.L_EYE = 1
        self.R_EYE = 2
        self.L_EAR = 3
        self.R_EAR = 4

        # 肩部
        self.L_SHOULDER = 5
        self.R_SHOULDER = 6

        # 手臂
        self.L_ELBOW = 7
        self.R_ELBOW = 8
        self.L_HAND = 9
        self.R_HAND = 10

        # 髋部
        self.L_HIP = 11
        self.R_HIP = 12

        # 膝盖
        self.L_KNEE = 13
        self.R_KNEE = 14

        # 脚踝
        self.L_ANKLE = 15
        self.R_ANKLE = 16

        # 颈部和锁骨
        self.NECK_BASE = 17
        self.R_CLAVICLE = 18
        self.L_CLAVICLE = 19

        # 手肘中点和手腕中点
        self.R_LELBOW = 20
        self.L_LELBOW = 21
        self.R_MELBOW = 22
        self.L_MELBOW = 23

        # 手腕中点和手腕外侧
        self.R_LWRIST = 24
        self.L_LWRIST = 25
        self.R_MWRIST = 26
        self.L_MWRIST = 27

        # ASIS和PSIS
        self.R_ASIS = 28
        self.L_ASIS = 29
        self.R_PSIS = 30
        self.L_PSIS = 31

        # 膝盖中点和膝盖外侧
        self.R_LKNEE = 32
        self.L_LKNEE = 33
        self.R_MKNEE = 34
        self.L_MKNEE = 35

        # 脚踝中点和脚踝外侧
        self.R_LANKLE = 36
        self.L_LANKLE = 37
        self.R_MANKLE = 38
        self.L_MANKLE = 39

        # 足部关键点
        self.R_5META = 40
        self.L_5META = 41
        self.R_TOE = 42
        self.L_TOE = 43
        self.R_BIG_TOE = 44
        self.L_BIG_TOE = 45
        self.L_CALC = 46
        self.R_CALC = 47

        # 脊柱
        self.C7 = 48
        self.L2 = 49
        self.T11 = 50
        self.T6 = 51

    # Reshape keypoints to (N, 3) format if needed
    def reshape_kp(self, kp):
        """
        将不同来源的关键点统一整理为 (N, 3) 格式。
        支持输入：
        1. (N, 2)：只有 x、y，自动补 confidence=1.0
        2. (N, 3)：x、y、confidence
        3. 一维列表：长度能被 2 或 3 整除时自动 reshape
        """
        if kp is None:
            raise ValueError("keypoints is None")

        kp = np.asarray(kp, dtype=float)

        if kp.ndim == 1:
            if kp.size % 3 == 0:
                kp = kp.reshape(-1, 3)
            elif kp.size % 2 == 0:
                kp = kp.reshape(-1, 2)
            else:
                raise ValueError(f"Invalid keypoints length: {kp.size}")

        if kp.ndim != 2:
            raise ValueError(f"Invalid keypoints shape: {kp.shape}")

        if kp.shape[1] == 2:
            conf = np.ones((kp.shape[0], 1), dtype=float)
            kp = np.concatenate([kp, conf], axis=1)
        elif kp.shape[1] >= 3:
            kp = kp[:, :3]
        else:
            raise ValueError(f"Invalid keypoints shape: {kp.shape}")

        return kp
    
    def has_points(self, kp, *idxs):
        # 判断当前关键点数组是否包含指定索引。
        return kp is not None and kp.ndim == 2 and kp.shape[0] > max(idxs)

    def _normalize_scores(self, kp, scores=None):
        # 优先使用外部 scores；没有时使用 kp 第 3 列作为置信度。
        kp = self.reshape_kp(kp)
        if scores is None:
            return kp, kp[:, 2]
        scores = np.asarray(scores, dtype=float).reshape(-1)
        return kp, scores
    
    # 1. Analyze shoulder asymmetry based on keypoints
    def analyze_shoulder_asymmetry(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_SHOULDER, self.R_SHOULDER):
            return None

        left_shoulder = kp[self.L_SHOULDER][:2]
        right_shoulder = kp[self.R_SHOULDER][:2]

        xL, yL = left_shoulder
        xR, yR = right_shoulder

        shoulder_height_diff = abs(yL - yR)
        shoulder_width = distance(left_shoulder, right_shoulder)
        SAI = shoulder_height_diff / (shoulder_width + 1e-6)

        # 分级
        if np.isfinite(SAI):
            if SAI < 0.02:
                level = "正常"
            elif SAI < 0.05:
                level = "轻度高低肩"
            elif SAI < 0.10:
                level = "中度高低肩"
            else:
                level = "重度高低肩"
        else:
            level = "异常"

        result = {
            "type": "shoulder_asymmetry",
            "left_shoulder": (float(xL), float(yL)),
            "right_shoulder": (float(xR), float(yR)),
            "shoulder_height_diff": float(shoulder_height_diff),
            "shoulder_width": float(shoulder_width),
            "SAI": float(SAI),
            "level": level
        }
        return result
    
    # 2. Analyze pelvic tilt based on keypoints
    def analyze_pelvic_tilt(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_HIP, self.R_HIP):
            return None
        left_hip = kp[self.L_HIP][:2]
        right_hip = kp[self.R_HIP][:2]

        xL, yL = left_hip
        xR, yR = right_hip

        # 倾斜角
        tilt_angle = line_angle(left_hip, right_hip)
        abs_tilt = abs(tilt_angle)

        # 分级
        if np.isfinite(abs_tilt):
            if abs_tilt < 3:
                level = "正常"
            elif abs_tilt < 5:
                level = "轻度骨盆倾斜"
            elif abs_tilt < 10:
                level = "中度骨盆倾斜"
            else:
                level = "重度骨盆倾斜"
        else:
            level = "异常"

        # 方向判断
        if yL < yR:
            direction = "左高右低"
        elif yL > yR:
            direction = "右高左低"
        else:
            direction = "左右等高"

        result = {
            "type": "pelvic_tilt",
            "left_hip": (float(xL), float(yL)),
            "right_hip": (float(xR), float(yR)),
            "abs_tilt_angle_deg": float(abs_tilt),
            "level": level,
            "direction": direction
        }
        return result
    
    # 3. Analyze head tilt based on keypoints
    def analyze_head_tilt(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.NOSE, self.C7):
            return None

        nose = kp[self.NOSE][:2]
        c7 = kp[self.C7][:2]
        x_nose, y_nose = nose
        x_c7, y_c7 = c7

        dx = x_nose - x_c7
        dy = y_nose - y_c7

        # 与竖直方向夹角
        if abs(dy) > 1e-6:
            tilt_angle = np.degrees(
                np.arctan(abs(dx) / abs(dy))
            )
        else:
            tilt_angle = None

        # 方向判断
        if dx > 0:
            direction = "头向左侧倾"
        elif dx < 0:
            direction = "头向右侧倾"
        else:
            direction = "头正直"

        # 分级
        if tilt_angle is not None and np.isfinite(tilt_angle):
            if tilt_angle < 2:
                level = "正常"
            elif tilt_angle < 5:
                level = "轻度"
            elif tilt_angle < 8:
                level = "中度"
            else:
                level = "重度"
        else:
            level = "无法判断"

        result = {
            "type": "head_tilt",
            "nose": tuple(nose),
            "c7": tuple(c7),
            "tilt_angle": float(tilt_angle) if tilt_angle is not None and np.isfinite(tilt_angle) else None,
            "level": level,
            "direction": direction,
        }

        return result    

    # 4. Analyze head rotation based on keypoints and confidence scores
    def analyze_head_rotation(self, kp, scores = None):
        kp, scores = self._normalize_scores(kp, scores)

        if not self.has_points(kp, self.L_EAR, self.R_EAR):
            return None

        l_score = float(scores[self.L_EAR])
        r_score = float(scores[self.R_EAR])

        diff = l_score - r_score
        abs_diff = abs(diff)

        # 方向
        if abs_diff < 0.15:
            direction = "正中"
        elif diff > 0:
            direction = "向右旋转"
        else:
            direction = "向左旋转"

        # 分级
        if abs_diff < 0.05:
            level = "正常"
        elif abs_diff < 0.15:
            level = "轻度旋转"
        elif abs_diff < 0.30:
            level = "中度旋转"
        else:
            level = "重度旋转"

        result = {
            "type": "head_rotation",
            "score_diff": float(diff),
            "level": level,
            "direction": direction,
            "left_score": l_score,
            "right_score": r_score,
        }
        return result
    
    # 5. Analyze pelvic rotation based on keypoints and confidence scores
    def analyze_pelvic_rotation(self, kp, scores = None):
        kp, scores = self._normalize_scores(kp, scores)

        if not self.has_points(kp, self.L_ASIS, self.R_ASIS):
            return None

        l_score = float(scores[self.L_ASIS])
        r_score = float(scores[self.R_ASIS])

        diff = l_score - r_score
        abs_diff = abs(diff)

        # 方向
        if abs_diff < 0.15:
            direction = "骨盆正向"
        elif diff > 0:
            direction = "骨盆向右旋转"   # 左侧更清晰
        else:
            direction = "骨盆向左旋转"   # 右侧更清晰

        # 分级
        if abs_diff < 0.05:
            level = "正常"
        elif abs_diff < 0.15:
            level = "轻度旋转"
        elif abs_diff < 0.30:
            level = "中度旋转"
        else:
            level = "重度旋转"

        result = {
            "type": "pelvic_rotation",
            "score_diff": float(diff),
            "level": level,
            "direction": direction,
            "left_score": l_score,
            "right_score": r_score,
        }

        return result
    
    # 6. Analyze leg length asymmetry based on keypoints
    def analyze_leg_length_asymmetry(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_HIP, self.R_HIP, self.L_ANKLE, self.R_ANKLE):
            return None

        left_hip = kp[self.L_HIP][:2]
        right_hip = kp[self.R_HIP][:2]
        left_ankle = kp[self.L_ANKLE][:2]
        right_ankle = kp[self.R_ANKLE][:2]

        xLH, yLH = left_hip
        xRH, yRH = right_hip
        xLA, yLA = left_ankle
        xRA, yRA = right_ankle

        # 下肢长度（y方向，图像坐标系向下为正）
        left_leg_length = yLA - yLH
        right_leg_length = yRA - yRH

        leg_length_diff = left_leg_length - right_leg_length

        # 肩宽归一化
        left_shoulder = kp[self.L_SHOULDER][:2]
        right_shoulder = kp[self.R_SHOULDER][:2]

        shoulder_width = distance(left_shoulder, right_shoulder)

        fli = abs(leg_length_diff) / (shoulder_width + 1e-6)

        # 方向判断
        if leg_length_diff > 0:
            direction = "左腿功能性偏长"
        elif leg_length_diff < 0:
            direction = "右腿功能性偏长"
        else:
            direction = "等长"

        # 分级
        if np.isfinite(fli):
            if fli < 0.03:
                level = "正常"
            elif fli < 0.05:
                level = "轻度功能性长短腿"
            elif fli < 0.08:
                level = "中度功能性长短腿"
            else:
                level = "重度功能性长短腿"
        else:
            level = "异常"

        result = {
            "type": "leg_length_asymmetry",
            "left_hip": (float(xLH), float(yLH)),
            "right_hip": (float(xRH), float(yRH)),
            "left_ankle": (float(xLA), float(yLA)),
            "right_ankle": (float(xRA), float(yRA)),
            "left_leg_length": float(left_leg_length),
            "right_leg_length": float(right_leg_length),
            "leg_length_diff": float(leg_length_diff),
            "fli": float(fli),
            "level": level,
            "direction": direction
        }

        return result

    # 7. Analyze foot progression angle (FPA) based on keypoints
    def analyze_fpa(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_ANKLE, self.R_ANKLE, self.L_BIG_TOE, self.R_BIG_TOE):
            return None

        xLA, yLA = kp[self.L_ANKLE][:2]
        xRA, yRA = kp[self.R_ANKLE][:2]
        xLT, yLT = kp[self.L_BIG_TOE][:2]
        xRT, yRT = kp[self.R_BIG_TOE][:2]
        # FPA计算函数
        def fpa(ax, ay):
            return np.degrees(np.arctan2(ax, ay))

        fpa_L = fpa(xLT - xLA, yLT - yLA)
        fpa_R = fpa(xRT - xRA, yRT - yRA)

        fpa_val = max(abs(fpa_L), abs(fpa_R))

        # 类型判断
        if abs(fpa_L) > abs(fpa_R):
            fpa_type = "脚内八" if fpa_L < 0 else "脚外八"
        else:
            fpa_type = "脚内八" if fpa_R > 0 else "脚外八"

        # 分级
        if fpa_val < 10:
            level = "正常"
        elif fpa_val < 20:
            level = "轻度"
        elif fpa_val < 30:
            level = "中度"
        else:
            level = "重度"

        result = {
            "type": "foot_progression_angle",
            "left_foot": (float(xLT), float(yLT)),
            "right_foot": (float(xRT), float(yRT)),
            "left_ankle": (float(xLA), float(yLA)),
            "right_ankle": (float(xRA), float(yRA)),
            "foot_type": fpa_type,
            "level": level,
            "left_fpa": float(fpa_L),
            "right_fpa": float(fpa_R),
            "fpa_val": float(fpa_val)
        }

        return result
    
    # 8. Analyze ankle inversion / eversion
    def analyze_ankle_inversion(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_ANKLE, self.R_ANKLE, self.L_BIG_TOE, self.R_BIG_TOE):
            return None

        xLK, yLK = kp[self.L_ANKLE][:2]
        xRK, yRK = kp[self.R_ANKLE][:2]
        xLA, yLA = kp[self.L_ANKLE][:2]
        xRA, yRA = kp[self.R_ANKLE][:2]
        xLT, yLT = kp[self.L_BIG_TOE][:2]
        xRT, yRT = kp[self.R_BIG_TOE][:2]

        inv_L = angle((xLK,yLK),(xLA,yLA),(xLT,yLT))
        inv_R = angle((xRK,yRK),(xRA,yRA),(xRT,yRT))

        inv = (inv_L + inv_R) / 2

        # 类型判断
        if inv < 160:
            foot_type = "足外翻"
        elif inv > 175:
            foot_type = "足内翻"
        else:
            foot_type = "正常"

        # 分级
        if inv < 150:
            level = "重度外翻"
        elif inv < 160:
            level = "轻中度外翻"
        elif inv > 180:
            level = "异常"
        else:
            level = "正常"

        result = {
            "type": "ankle_inversion",
            "foot_type": foot_type,
            "level": level,
            "avg_angle": float(inv),
            "left_angle": float(inv_L),
            "right_angle": float(inv_R),
            "left_knee": (float(xLK), float(yLK)),
            "right_knee": (float(xRK), float(yRK)),
            "left_ankle": (float(xLA), float(yLA)),
            "right_ankle": (float(xRA), float(yRA)),
            "left_toe": (float(xLT), float(yLT)),
            "right_toe": (float(xRT), float(yRT)),
        }
        return result   

    # 9. Analyze knee valgus/varus based on keypoints
    def analyze_knee_valgus_varus(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_HIP, self.R_HIP, self.L_KNEE, self.R_KNEE, self.L_ANKLE, self.R_ANKLE):   
            return None
        
        xLH, yLH = kp[self.L_HIP][:2]
        xLK, yLK = kp[self.L_KNEE][:2]
        xLA, yLA = kp[self.L_ANKLE][:2]
        xRH, yRH = kp[self.R_HIP][:2]
        xRK, yRK = kp[self.R_KNEE][:2]
        xRA, yRA = kp[self.R_ANKLE][:2]


        # 左腿角度
        v1_x_L = xLK - xLH
        v1_y_L = yLK - yLH
        v1_norm_L = np.sqrt(v1_x_L**2 + v1_y_L**2)

        v2_x_L = xLA - xLK
        v2_y_L = yLA - yLK
        v2_norm_L = np.sqrt(v2_x_L**2 + v2_y_L**2)

        if v1_norm_L > 1e-6 and v2_norm_L > 1e-6:
            dot_L = v1_x_L * v2_x_L + v1_y_L * v2_y_L
            cos_L = dot_L / (v1_norm_L * v2_norm_L)
            cos_L = np.clip(cos_L, -1.0, 1.0)
            angle_L = np.degrees(np.arccos(cos_L))
            valgus_L = 180 - angle_L
        else:
            valgus_L = float("inf")

        # 右腿角度
        v1_x_R = xRK - xRH
        v1_y_R = yRK - yRH
        v1_norm_R = np.sqrt(v1_x_R**2 + v1_y_R**2)

        v2_x_R = xRA - xRK
        v2_y_R = yRA - yRK
        v2_norm_R = np.sqrt(v2_x_R**2 + v2_y_R**2)

        if v1_norm_R > 1e-6 and v2_norm_R > 1e-6:
            dot_R = v1_x_R * v2_x_R + v1_y_R * v2_y_R
            cos_R = dot_R / (v1_norm_R * v2_norm_R)
            cos_R = np.clip(cos_R, -1.0, 1.0)
            angle_R = np.degrees(np.arccos(cos_R))
            valgus_R = 180 - angle_R
        else:
            valgus_R = float("inf")

        # 左腿
        t_L = max(0, min(1, ((xLK - xLH) * (xLA - xLH) + (yLK - yLH) * (yLA - yLH)) / 
                       ((xLA - xLH)**2 + (yLA - yLH)**2 + 1e-6)))
        line_x_L = xLH + t_L * (xLA - xLH)
        d_L = xLK - line_x_L

        # 右腿
        t_R = max(0, min(1, ((xRK - xRH) * (xRA - xRH) + (yRK - yRH) * (yRA - yRH)) / 
                       ((xRA - xRH)**2 + (yRA - yRH)**2 + 1e-6)))
        line_x_R = xRH + t_R * (xRA - xRH)
        d_R = xRK - line_x_R

        # 主方向
        if abs(d_L) > abs(d_R):
            direction = "膝外翻" if d_L > 0 else "膝内翻"
        else:
            direction = "膝外翻" if d_R < 0 else "膝内翻"

        # 分级
        inner_Lleg_angle = 180 - valgus_L
        inner_Rleg_angle = 180 - valgus_R
        inner_angle = max(inner_Lleg_angle, inner_Rleg_angle)

        if np.isfinite(inner_angle):
            if inner_angle < 3:
                level = "正常"
            elif inner_angle < 5:
                level = "轻度膝内外翻"
            elif inner_angle < 10:
                level = "中度膝内外翻"
            else:
                level = "重度膝内外翻"
        else:
            level = "异常"

        result = {
            "type": "knee_valgus_varus",
            "left_knee": (float(xLK), float(yLK)),
            "right_knee": (float(xRK), float(yRK)),
            "left_angle": float(abs(valgus_L)),
            "right_angle": float(abs(valgus_R)),
            "angle": float(180 - inner_angle),
            "direction": direction,
            "level": level,
        }

        return result    

    # 10. Analyze head forward posture based on keypoints
    def analyze_head_forward(self, kp):
        kp = self.reshape_kp(kp)

        if not self.has_points(kp, self.NOSE, self.L_SHOULDER, self.R_SHOULDER):
            return None

        # 鼻子
        x_nose, y_nose = kp[self.NOSE][:2]
        # 双肩
        x_LS, y_LS = kp[self.L_SHOULDER][:2]
        x_RS, y_RS = kp[self.R_SHOULDER][:2]
        # C7 = 双肩中点
        x_c7 = (x_LS + x_RS) / 2
        y_c7 = (y_LS + y_RS) / 2
        # 头部点
        x_head = x_nose
        y_head = y_nose

        # 向量
        dx = abs(x_head - x_c7)
        dy = abs(y_head - y_c7)

        # CVA角度
        if dx > 1e-6:
            cva = np.degrees(np.arctan(dy / dx))
        else:
            cva = 90.0

        # 方向
        if x_head > x_c7:
            direction = "头向右前"
        elif x_head < x_c7:
            direction = "头向左前"
        else:
            direction = "头部居中"

        # 风险等级
        if cva >= 50:
            level = "正常"
        elif cva >= 45:
            level = "轻度头前伸"
        elif cva >= 40:
            level = "中度头前伸"
        else:
            level = "重度头前伸"

        result = {
            "type": "head_forward",
            "CVA": float(cva),
            "level": level,
            "direction": direction,
            "nose": (x_head, y_head),
            "c7": (x_c7, y_c7),
            "dx": float(dx),
            "dy": float(dy)
        }
        return result

    # 11. Analyze round shoulder based on keypoints
    def analyze_round_shoulder(self, kp):
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_SHOULDER, self.R_SHOULDER, self.L_EAR, self.R_EAR):
            return None

        # 肩 & 耳
        x_LS, y_LS = kp[self.L_SHOULDER][:2]
        x_RS, y_RS = kp[self.R_SHOULDER][:2]

        x_LE, y_LE = kp[self.L_EAR][:2]
        x_RE, y_RE = kp[self.R_EAR][:2]

        # 判断侧向
        if abs(x_LE - x_LS) > abs(x_RE - x_RS):
            side = "left"
            x_sh, y_sh = x_LS, y_LS
            x_ear, y_ear = x_LE, y_LE
        else:
            side = "right"
            x_sh, y_sh = x_RS, y_RS
            x_ear, y_ear = x_RE, y_RE

        # 归一化（颈部高度）
        neck_h = abs(y_ear - y_sh) + 1e-6

        # SED（肩前移）
        dx = x_sh - x_ear
        sed = abs(dx / neck_h)

        # 分级
        if sed < 0.03:
            level = "正常"
        elif sed < 0.08:
            level = "轻度圆肩"
        elif sed < 0.15:
            level = "中度圆肩"
        else:
            level = "重度圆肩"

        result ={
            "type": "round_shoulder",
            "side": side,
            "level": level,
            "SED": float(sed),
            "shoulder_forward_px": float(dx),
            "neck_height": float(neck_h),
            "shoulder": (x_sh, y_sh),
            "ear": (x_ear, y_ear)
        }
        return result

    # 12. Analyze spine Cobb angle based on keypoints
    def analyze_spine_cobb(self, kp):
        kp = self.reshape_kp(kp)

        if not self.has_points(kp, self.C7, self.T6, self.T11, self.L2):
            return None

        spine_points = [
            kp[self.C7][:2],
            kp[self.T6][:2],
            kp[self.T11][:2],
            kp[self.L2][:2],
        ]

        labels = ["C7", "T6", "T11", "L2"]

        angles = []

        for i in range(len(spine_points) - 2):
            p1 = spine_points[i]
            p2 = spine_points[i + 1]
            p3 = spine_points[i + 2]

            angle = angle(p1, p2, p3)


            if angle > 90:
                angle = 180 - angle

            angles.append(angle)

        cobb = max(angles)

        # 分级
        if cobb < 10:
            level = "正常"
        elif cobb < 20:
            level = "轻度侧弯"
        elif cobb < 40:
            level = "中度侧弯"
        else:
            level = "重度侧弯"

        result = {
            "type": "spine_cobb",
            "cobb_angle": float(cobb),
            "level": level,
            "angles": angles,
            "spine_points": spine_points,
            "labels": labels
        }

        return result

    # 13. Analyze thoracic kyphosis based on keypoints
    def analyze_thoracic_kyphosis(self, kp):
        """侧视图胸椎后凸风险：基于 C7-T11-L2 的夹角近似评估。"""
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.C7, self.T11, self.L2):
            return None

        c7 = kp[self.C7][:2]
        t11 = kp[self.T11][:2]
        l2 = kp[self.L2][:2]
        kyphosis_angle = 180.0 - angle(c7, t11, l2)
        kyphosis_angle = abs(float(kyphosis_angle))

        if kyphosis_angle < 10:
            level = "正常"
        elif kyphosis_angle < 20:
            level = "轻度胸椎后凸"
        elif kyphosis_angle < 35:
            level = "中度胸椎后凸"
        else:
            level = "重度胸椎后凸"

        result = {
                "type": "thoracic_kyphosis",
                "kyphosis_angle": float(kyphosis_angle),
                "level": level,
                "c7": (float(c7[0]), float(c7[1])),
                "t11": (float(t11[0]), float(t11[1])),
                "l2": (float(l2[0]), float(l2[1])),
        }
        return result   

    # 14. Analyze pelvic anterior/posterior tilt based on keypoints
    def analyze_pelvic_anterior_posterior_tilt(self, kp):
        """侧视图骨盆前倾/后倾：优先使用 ASIS/PSIS，按骨盆线与水平线夹角近似。"""
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_ASIS, self.R_ASIS, self.L_PSIS, self.R_PSIS):
            return None

        asis = (kp[self.L_ASIS][:2] + kp[self.R_ASIS][:2]) / 2.0
        psis = (kp[self.L_PSIS][:2] + kp[self.R_PSIS][:2]) / 2.0
        tilt_angle = float(line_angle(asis, psis))
        abs_tilt = abs(tilt_angle)

        if abs_tilt < 8:
            level = "正常"
        elif abs_tilt < 15:
            level = "轻度"
        elif abs_tilt < 25:
            level = "中度"
        else:
            level = "重度"

        direction = "骨盆前倾" if tilt_angle > 0 else "骨盆后倾"

        result = {
            "type": "pelvic_anterior_posterior_tilt",
            "tilt_angle": float(tilt_angle),
            "abs_tilt_angle": float(abs_tilt),
            "level": level,
            "direction": direction,
            "asis_mid": (float(asis[0]), float(asis[1])),
            "psis_mid": (float(psis[0]), float(psis[1])),
        }
        return result

    def analyze_lumbar_lordosis(self, kp):
        """侧视图腰椎前凸风险：基于 T11-L2-髋中点夹角近似。"""
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.T11, self.L2, self.L_HIP, self.R_HIP):
            return None

        t11 = kp[self.T11][:2]
        l2 = kp[self.L2][:2]
        hip_mid = (kp[self.L_HIP][:2] + kp[self.R_HIP][:2]) / 2.0
        lordosis_angle = 180.0 - angle(t11, l2, hip_mid)
        lordosis_angle = abs(float(lordosis_angle))

        if lordosis_angle < 10:
            level = "正常"
        elif lordosis_angle < 20:
            level = "轻度腰椎前凸"
        elif lordosis_angle < 35:
            level = "中度腰椎前凸"
        else:
            level = "重度腰椎前凸"

        result = {
            "type": "lumbar_lordosis",
            "lordosis_angle": float(lordosis_angle),
            "level": level,
            "t11": (float(t11[0]), float(t11[1])),
            "l2": (float(l2[0]), float(l2[1])),
            "hip_mid": (float(hip_mid[0]), float(hip_mid[1])),
        }
        return result

    # 15. Analyze knee hyperextension based on keypoints
    def analyze_knee_hyperextension(self, kp):
        """侧视图膝关节超伸风险：基于髋-膝-踝夹角近似。"""
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_HIP, self.R_HIP, self.L_KNEE, self.R_KNEE, self.L_ANKLE, self.R_ANKLE):
            return None

        left_angle = angle(kp[self.L_HIP][:2], kp[self.L_KNEE][:2], kp[self.L_ANKLE][:2])
        right_angle = angle(kp[self.R_HIP][:2], kp[self.R_KNEE][:2], kp[self.R_ANKLE][:2])
        knee_angle = float(max(left_angle, right_angle))

        if knee_angle < 170:
            level = "正常"
        elif knee_angle < 176:
            level = "轻度膝关节超伸风险"
        else:
            level = "中重度膝关节超伸风险"

        result = {
            "type": "knee_hyperextension",
            "knee_angle": float(knee_angle),
            "left_angle": float(left_angle),
            "right_angle": float(right_angle),
            "level": level, 
        }
        return result

    # 16. Analyze center of mass shift based on keypoints
    def analyze_center_shift(self, kp):
        """人体重心偏移近似：肩中点-髋中点相对踝中点的水平偏移。"""
        kp = self.reshape_kp(kp)
        if not self.has_points(kp, self.L_SHOULDER, self.R_SHOULDER, self.L_HIP, self.R_HIP, self.L_ANKLE, self.R_ANKLE):
            return None

        shoulder_mid = (kp[self.L_SHOULDER][:2] + kp[self.R_SHOULDER][:2]) / 2.0
        hip_mid = (kp[self.L_HIP][:2] + kp[self.R_HIP][:2]) / 2.0
        ankle_mid = (kp[self.L_ANKLE][:2] + kp[self.R_ANKLE][:2]) / 2.0
        body_mid = (shoulder_mid + hip_mid) / 2.0
        support_width = distance(kp[self.L_ANKLE][:2], kp[self.R_ANKLE][:2]) + 1e-6
        shift_ratio = abs(body_mid[0] - ankle_mid[0]) / support_width

        if shift_ratio < 0.05:
            level = "正常"
        elif shift_ratio < 0.10:
            level = "轻度重心偏移"
        elif shift_ratio < 0.20:
            level = "中度重心偏移"
        else:
            level = "重度重心偏移"

        direction = "向右偏移" if body_mid[0] > ankle_mid[0] else "向左偏移"

        result = {
            "type": "center_shift",
            "shift_ratio": float(shift_ratio),
            "level": level,
            "direction": direction,
            "body_mid": (float(body_mid[0]), float(body_mid[1])),
            "ankle_mid": (float(ankle_mid[0]), float(ankle_mid[1])),
        }
        return result
