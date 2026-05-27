import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

class Visualization:
    def __init__(self):
        self.font = self._load_font(20)
        self.font_small = self._load_font(14)

    def _load_font(self, size):
        try:
            return ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", size)
        except:
            try:
                return ImageFont.truetype("C:\\Windows\\Fonts\\simsun.ttc", size)
            except:
                return ImageFont.load_default()
    
    def draw_shoulder_asymmetry(self, image, result) -> Image.Image:
        xL, yL = result["left_shoulder"]
        xR, yR = result["right_shoulder"]
        height_diff = result["shoulder_height_diff"]
        width = result["shoulder_width"]
        sai = result["SAI"]
        level = result["level"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 画肩线
        cv2.line(vis_bgr, (int(xL), int(yL)), (int(xR), int(yR)), (0, 0, 255), 1, cv2.LINE_AA)
        # 画水平线
        mid_x = int((xL + xR) / 2)
        lowest_y = int(max(yL, yR))   # 最低肩点
        ref_len = 150
        cv2.line(vis_bgr, (mid_x - ref_len, lowest_y), (mid_x + ref_len, lowest_y), (200, 200, 200), 1, cv2.LINE_AA)

        # 关键点
        cv2.circle(vis_bgr, (int(xL), int(yL)), 4, (0, 255, 0), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (int(xR), int(yR)), 4, (0, 255, 0), -1, cv2.LINE_AA)
        # 标注
        cv2.putText(vis_bgr, f"L:{yL:.1f}", (int(xL) - 40, int(yL) - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText( vis_bgr, f"R:{yR:.1f}", (int(xR) + 10, int(yR) - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

        # 转 PIL
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"SAI={sai:.4f}"
        txt2 = f"高低肩: {level}"
        txt3 = f"高度差: {height_diff:.2f}px | 肩宽: {width:.2f}px"
        draw.text((10, 10), txt1, fill=(255, 255, 255), font=self.font)
        draw.text((10, 50), txt2, fill=(255, 255, 255), font=self.font_small)
        draw.text((10, 80), txt3, fill=(255, 255, 255), font=self.font_small)

        return pil_img
    
    def draw_pelvic_tilt(self, image, result) -> Image.Image:
        xLH, yLH = result["left_hip"]
        xRH, yRH = result["right_hip"]
        abs_tilt = result["abs_tilt_angle_deg"]
        direction = result["direction"]
        level = result["level"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 画骨盆连线
        cv2.line(vis_bgr, (round(xLH), round(yLH)), (round(xRH), round(yRH)), (0, 255, 255), 1, cv2.LINE_AA)

        # 关键点
        cv2.circle(vis_bgr, (round(xLH), round(yLH)), 4, (255, 0, 0), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (round(xRH), round(yRH)), 4, (0, 0, 255), -1, cv2.LINE_AA)

        # 中点
        mid_x = int((xLH + xRH) / 2)

        # 最低髋点
        if yLH > yRH:
            lowest_x = int(xLH)
            lowest_y = int(yLH)
        else:
            lowest_x = int(xRH)
            lowest_y = int(yRH)

        # 水平参考线
        ref_len = 150
        cv2.line(vis_bgr, (mid_x - ref_len, lowest_y), (mid_x + ref_len, lowest_y), (200, 200, 200), 1, cv2.LINE_AA)

        # 角度弧线
        if np.isfinite(abs_tilt) and abs_tilt > 0.1 and direction != "左右等高":
            arc_radius = 80
            arc_center = (lowest_x, lowest_y)
            if direction == "右高左低":
                start_angle = 180 + abs_tilt
                end_angle = 180
            else:
                start_angle = 360
                end_angle = 360 - abs_tilt
            cv2.ellipse(vis_bgr, arc_center, (arc_radius, arc_radius), 0, int(start_angle), int(end_angle), (0, 255, 0), 2)

            # 角度文字位置
            angle_label_dist = arc_radius + 20
            mid_angle = (start_angle + end_angle) / 2
            angle_label_x = int(
                arc_center[0] + angle_label_dist * np.cos(np.radians(mid_angle))
            )
            angle_label_y = int(
                arc_center[1] + angle_label_dist * np.sin(np.radians(mid_angle))
            )
            cv2.putText(vis_bgr, f"{abs_tilt:.2f}", (angle_label_x - 20, angle_label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 标注左右高度
        cv2.putText(vis_bgr, f"L:{yLH:.1f}", (int(xLH) - 40, int(yLH) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(vis_bgr, f"R:{yRH:.1f}", (int(xRH) + 10, int(yRH) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 转 PIL
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"骨盆倾斜角: {abs_tilt:.2f}°"
        txt2 = f"骨盆倾斜: {direction} - {level}"
        txt3 = f"L:{yLH:.1f}px  R:{yRH:.1f}px"
        
        draw.text((10, 10), txt1, fill=(255, 255, 255), font=self.font)
        draw.text((10, 50), txt2, fill=(255, 255, 255), font=self.font_small)
        draw.text((10, 80), txt3, fill=(255, 255, 255), font=self.font_small)

        return pil_img
    
    def draw_head_tilt(self, image, result):
        nose = result["nose"]
        c7 = result["c7"]
        tilt_angle = result["tilt_angle"]
        level = result["level"]
        direction = result["direction"]

        x_nose, y_nose = nose
        x_c7, y_c7 = c7

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # C7点和鼻尖
        cv2.circle(vis_bgr, (int(x_c7), int(y_c7)), 4, (0, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (int(x_nose), int(y_nose)), 4, (0, 255, 255), -1, cv2.LINE_AA)

        # 头颈线
        cv2.line(vis_bgr, (int(x_c7), int(y_c7)), (int(x_nose), int(y_nose)), (0, 0, 255), 1, cv2.LINE_AA)

        # 竖直参考线
        length = int(abs(y_nose - y_c7)) + 50
        cv2.line(vis_bgr, (int(x_c7), int(y_c7 - length)),(int(x_c7), int(y_c7 + length)), (150, 150, 150), 1, cv2.LINE_AA)

        # 角度弧线
        if np.isfinite(tilt_angle):
            dx = x_nose - x_c7
            dy = y_nose - y_c7
            angle_vec = np.degrees(np.arctan2(dy, dx))
            angle_vertical = -90

            if direction == "头向左侧倾":
                start_angle = angle_vec
                end_angle = angle_vertical
            else:
                start_angle = angle_vertical
                end_angle = angle_vec

            cv2.ellipse(vis_bgr, (int(x_c7), int(y_c7)), (40, 40), 0, start_angle, end_angle, (0, 255, 0), 2)

            # 角度文字
            mid_angle = (start_angle + end_angle) / 2
            r = 55
            rad = np.radians(mid_angle)
            tx = int(x_c7 + r * np.cos(rad))
            ty = int(y_c7 + r * np.sin(rad))
            cv2.putText(vis_bgr, f"{tilt_angle:.1f}", (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 100),2)

        # 转 PIL 写中文
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"头部侧倾: {level}"
        txt2 = f"侧倾角: {tilt_angle:.2f}° | {direction}"

        draw.text((10, 10), txt1, fill=(255,255,255), font=self.font)
        draw.text((10, 50), txt2, fill=(255,255,255), font=self.font_small)

        return pil_img

    def draw_head_rotation(self, image, result):
        level = result["level"]
        direction = result["direction"]
        l_score = result["left_score"]
        r_score = result["right_score"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 转 PIL 写中文
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"头旋转评估: {level}"
        txt2 = f"{direction}"
        txt3 = f"L={l_score:.2f}  R={r_score:.2f}"

        draw.text((10, 10), txt1, fill=(255,255,255), font=self.font)
        draw.text((10, 45), txt2, fill=(255,255,255), font=self.font_small)
        draw.text((10, 70), txt3, fill=(180,180,180), font=self.font_small)

        return pil_img

    def draw_pelvic_rotation(self, image, result):
        level = result["level"]
        direction = result["direction"]
        l_score = result["left_score"]
        r_score = result["right_score"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"骨盆旋转: {level}"
        txt2 = f"{direction}"
        txt3 = f"L={l_score:.2f}  R={r_score:.2f}"

        draw.text((10, 110), txt1, fill=(255,255,255), font=self.font)
        draw.text((10, 145), txt2, fill=(255,255,255), font=self.font_small)
        draw.text((10, 170), txt3, fill=(180,180,180), font=self.font_small)

        return pil_img
    
    def draw_leg_length_asymmetry(self, image, result) -> Image.Image:
        xLH, yLH = result["left_hip"]
        xRH, yRH = result["right_hip"]
        xLA, yLA = result["left_ankle"]
        xRA, yRA = result["right_ankle"]
        leg_L = result["left_leg_length"]
        leg_R = result["right_leg_length"]
        delta = result["leg_length_diff"]
        fli = result["fli"]
        level = result["level"]
        direction = result["direction"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 左腿（髋-踝）
        xL = int(xLH)
        cv2.line(vis_bgr, (xL, int(yLH)), (xL, int(yLA)), (255, 100, 100), 2, cv2.LINE_AA)
        cv2.circle(vis_bgr, (xL, int(yLH)), 4, (255, 100, 100), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (xL, int(yLA)), 4, (100, 255, 100), -1, cv2.LINE_AA)
        cv2.putText(vis_bgr, f"L:{leg_L:.1f}px", (xL + 10, int((yLH + yLA) / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 1, cv2.LINE_AA)

        # 右腿（髋-踝）
        xR = int(xRH)
        cv2.line(vis_bgr, (xR, int(yRH)), (xR, int(yRA)), (100, 100, 255), 2, cv2.LINE_AA)
        cv2.circle(vis_bgr, (xR, int(yRH)), 4, (100, 100, 255), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (xR, int(yRA)), 4, (100, 255, 100), -1, cv2.LINE_AA)
        cv2.putText(vis_bgr, f"R:{leg_R:.1f}px", (xR + 10, int((yRH + yRA) / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 255), 1, cv2.LINE_AA)

        # 转 PIL（中文层）
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"功能性长短腿 = {level}"
        txt2 = f"{direction}"
        txt3 = f"Δ={delta:.2f}px | FLI={fli:.4f}"
        draw.text((10, 10), txt1, fill=(255, 255, 255), font=self.font)
        draw.text((10, 45), txt2, fill=(255, 255, 255), font=self.font_small)
        draw.text((10, 80), txt3, fill=(255, 255, 255), font=self.font_small)

        return pil_img

    def draw_fpa(self, image, result) -> Image.Image:
        xLT, yLT = result["left_foot"]
        xRT, yRT = result["right_foot"]
        xLA, yLA = result["left_ankle"]
        xRA, yRA = result["right_ankle"]
        fpa_type = result["foot_type"]
        level = result["level"]
        fpa_val = result["fpa_val"]
        left_fpa = result["left_fpa"]
        right_fpa = result["right_fpa"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 左脚方向线
        cv2.line(vis_bgr, (int(xLA), int(yLA)), (int(xLT), int(yLT)), (255, 100, 0), 2, cv2.LINE_AA)
        # 右脚方向线
        cv2.line(vis_bgr, (int(xRA), int(yRA)), (int(xRT), int(yRT)), (0, 100, 255), 2, cv2.LINE_AA)
        # 踝部垂直线
        line_len = 80
        cv2.line(vis_bgr, (int(xLA), int(yLA-line_len)), (int(xLA), int(yLA+line_len)), (200,200,200), 1, cv2.LINE_AA)
        cv2.line(vis_bgr, (int(xRA), int(yRA-line_len)), (int(xRA), int(yRA+line_len)), (200,200,200), 1, cv2.LINE_AA)

        # 关键点
        cv2.circle(vis_bgr, (int(xLT), int(yLT)), 4, (0, 255, 0), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (int(xRT), int(yRT)), 4, (0, 255, 0), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (int(xLA), int(yLA)), 4, (255, 0, 0), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (int(xRA), int(yRA)), 4, (255, 0, 0), -1, cv2.LINE_AA)

        # 左脚角度弧线
        vertical_L = (xLA, yLA - 50)
        v1 = np.array(vertical_L) - np.array([xLA, yLA])
        v2 = np.array((xLT, yLT)) - np.array([xLA, yLA])
        a1 = np.degrees(np.arctan2(v1[1], v1[0]))
        a2 = np.degrees(np.arctan2(v2[1], v2[0]))

        start = min(a1, a2) + 180
        end = max(a1, a2)
        cv2.ellipse(vis_bgr, (int(xLA), int(yLA)), (35, 35), 0, start, end, (0,255,255), 2,cv2.LINE_AA)
        text_x_L = int(xLA + 20)
        text_y_L = int(yLA - 20)
        cv2.putText(vis_bgr, f"{abs(left_fpa):.1f}", (text_x_L, text_y_L), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1, cv2.LINE_AA)

        # 右脚角度弧线
        vertical_R = (xRA, yRA - 50)
        v1 = np.array(vertical_R) - np.array([xRA, yRA])
        v2 = np.array((xRT, yRT)) - np.array([xRA, yRA])
        a1 = np.degrees(np.arctan2(v1[1], v1[0]))
        a2 = np.degrees(np.arctan2(v2[1], v2[0]))

        start = min(a1, a2) + 180
        end = max(a1, a2)
        cv2.ellipse(vis_bgr, (int(xRA), int(yRA)), (35, 35), 0, start, end, (0,255,255), 2,cv2.LINE_AA)
        text_x_R = int(xRA + 20)
        text_y_R = int(yRA - 20)
        cv2.putText(vis_bgr, f"{abs(right_fpa):.1f}", (text_x_R, text_y_R), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1, cv2.LINE_AA)

        # 转 PIL
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"脚部姿态: {level}"
        txt2 = f"FPA: {fpa_val:.2f}°"
        txt3 = f"类型：{fpa_type}"

        draw.text((10, 10), txt1, fill=(255, 255, 255), font=self.font)
        draw.text((10, 40), txt2, fill=(255, 255, 255), font=self.font)
        if level != "正常":
            draw.text((10, 70), txt3, fill=(255, 255, 255), font=self.font)

        return pil_img

    def draw_ankle_inversion(self, image, result) -> Image.Image:
        xLK, yLK = result["left_knee"]
        xRK, yRK = result["right_knee"]
        xLA, yLA = result["left_ankle"]
        xRA, yRA = result["right_ankle"]
        xLT, yLT = result["left_toe"]
        xRT, yRT = result["right_toe"]
        inv_L = result["left_angle"]
        inv_R = result["right_angle"]
        foot_type = result["foot_type"]
        level = result["level"]
        inv = result["avg_angle"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 小腿
        cv2.line(vis_bgr,(int(xLK),int(yLK)),(int(xLA),int(yLA)),(255,0,0),2,cv2.LINE_AA)
        cv2.line(vis_bgr,(int(xRK),int(yRK)),(int(xRA),int(yRA)),(0,0,255),2,cv2.LINE_AA)
        # 足
        cv2.line(vis_bgr,(int(xLA),int(yLA)),(int(xLT),int(yLT)),(255,100,0),2,cv2.LINE_AA)
        cv2.line(vis_bgr,(int(xRA),int(yRA)),(int(xRT),int(yRT)),(0,100,255),2,cv2.LINE_AA)

        # 关键点
        for x,y in [
            (xLT,yLT),(xRT,yRT),
            (xLA,yLA),(xRA,yRA),
            (xLK,yLK),(xRK,yRK)
        ]:
            cv2.circle(vis_bgr,(int(x),int(y)),4,(0,255,0),-1,cv2.LINE_AA)

        # 左脚角度弧线
        v1 = np.array((xLK, yLK)) - np.array((xLA, yLA))
        v2 = np.array((xLT, yLT)) - np.array((xLA, yLA))
        a1 = np.degrees(np.arctan2(v1[1], v1[0]))
        a2 = np.degrees(np.arctan2(v2[1], v2[0]))
        start = min(a1, a2)
        end = max(a1, a2)
        cv2.ellipse(
            vis_bgr,
            (int(xLA), int(yLA)),
            (35, 35),
            0,
            start,
            end,
            (0,255,255),
            2,
            cv2.LINE_AA
        )
        cv2.putText(
            vis_bgr,
            f"{inv_L:.1f}",
            (int(xLA + 5), int(yLA - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0,255,255),
            1,
            cv2.LINE_AA
        )

        # 右脚角度弧线
        v1 = np.array((xRK, yRK)) - np.array((xRA, yRA))
        v2 = np.array((xRT, yRT)) - np.array((xRA, yRA))
        a1 = np.degrees(np.arctan2(v1[1], v1[0]))
        a2 = np.degrees(np.arctan2(v2[1], v2[0]))
        start = min(a1, a2) + 360
        end = max(a1, a2)
        cv2.ellipse(
            vis_bgr,
            (int(xRA), int(yRA)),
            (35, 35),
            0,
            start,
            end,
            (0,255,255),
            2,
            cv2.LINE_AA
        )
        cv2.putText(
            vis_bgr,
            f"{inv_R:.1f}",
            (int(xRA + 5), int(yRA - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0,255,255),
            1,
            cv2.LINE_AA
        )

        # 转 PIL
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"足内翻/外翻: {foot_type}"
        txt2 = f"角度: {inv:.2f}°"
        txt3 = f"等级: {level}"

        draw.text((10,10), txt1, fill=(255,255,255), font=self.font)
        draw.text((10,40), txt2, fill=(255,255,255), font=self.font_small)
        draw.text((10,70), txt3, fill=(255,255,255), font=self.font_small)

        return pil_img
    
    def draw_head_forward(self, image, result) -> Image.Image:
        x_head, y_head = result["nose"]
        x_c7, y_c7 = result["c7"]
        cva = result["CVA"]
        level = result["level"]
        direction = result["direction"]
        dx = result["dx"]
        dy = result["dy"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 头颈力线
        cv2.line(
            vis_bgr,
            (int(x_c7), int(y_c7)),
            (int(x_head), int(y_head)),
            (255, 100, 0),
            2,
            cv2.LINE_AA
        )

        # 水平参考线
        ref_len = 120
        cv2.line(
            vis_bgr,
            (int(x_c7 - ref_len), int(y_c7)),
            (int(x_c7 + ref_len), int(y_c7)),
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        # 垂直参考线
        cv2.line(
            vis_bgr,
            (int(x_c7), int(y_c7 - ref_len)),
            (int(x_c7), int(y_c7 + ref_len)),
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        # 关键点
        cv2.circle(vis_bgr, (int(x_head), int(y_head)), 5, (0, 200, 255), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (int(x_c7), int(y_c7)), 5, (0, 255, 255), -1, cv2.LINE_AA)

        # CVA角度弧线
        arc_r = 40
        if x_head >= x_c7:
            start = int(360 - cva)
            end = 360
        else:
            start = 180
            end = int(180 + cva)

        cv2.ellipse(
            vis_bgr,
            (int(x_c7), int(y_c7)),
            (arc_r, arc_r),
            0,
            start,
            end,
            (100, 200, 100),
            2,
            cv2.LINE_AA
        )

        # 角度文字
        mid = (start + end) / 2
        tx = int(x_c7 + (arc_r + 20) * np.cos(np.radians(mid)))
        ty = int(y_c7 + (arc_r + 20) * np.sin(np.radians(mid)))

        cv2.putText(
            vis_bgr,
            f"{cva:.1f}°",
            (tx, ty),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (100, 200, 100),
            2,
            cv2.LINE_AA
        )

        # 转 PIL
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"CVA={cva:.2f}°"
        txt2 = f"头前伸: {level}"
        txt3 = f"{direction} | dx={dx:.1f}px dy={dy:.1f}px"
        draw.text((10, 10), txt1, fill=(255, 255, 255), font=self.font)
        draw.text((10, 50), txt2, fill=(255, 255, 255), font=self.font_small)
        draw.text((10, 80), txt3, fill=(255, 255, 255), font=self.font_small)

        return pil_img
    
    def draw_round_shoulder(self, image, result) -> Image.Image:
        x_sh, y_sh = result["shoulder"]
        x_ear, y_ear = result["ear"]
        sed = result["SED"]
        level = result["level"]
        side = result["side"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 关键点
        cv2.circle(vis_bgr, (int(x_sh), int(y_sh)), 6, (255, 200, 0), -1, cv2.LINE_AA)
        cv2.circle(vis_bgr, (int(x_ear), int(y_ear)), 6, (0, 255, 255), -1, cv2.LINE_AA)

        # 垂直参考线
        ref_len = 200

        cv2.line(
            vis_bgr,
            (int(x_sh), int(y_sh - ref_len)),
            (int(x_sh), int(y_sh + ref_len)),
            (150, 150, 150),
            1,
            cv2.LINE_AA
        )

        cv2.line(
            vis_bgr,
            (int(x_ear), int(y_ear - ref_len)),
            (int(x_ear), int(y_ear + ref_len)),
            (150, 150, 150),
            1,
            cv2.LINE_AA
        )

        # 圆肩箭头
        cv2.arrowedLine(
            vis_bgr,
            (int(x_ear), int(y_sh)),
            (int(x_sh), int(y_sh)),
            (255, 200, 0),
            2,
            tipLength=0.2
        )

        # PIL文字

        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"圆肩: {level}"
        txt2 = f"SED={sed:.3f}"
        txt3 = f"{side}侧 | 肩前移={result['shoulder_forward_px']:.1f}px"

        draw.text((10, 10), txt1, fill=(255, 255, 255), font=self.font)
        draw.text((10, 50), txt2, fill=(255, 255, 255), font=self.font_small)
        draw.text((10, 80), txt3, fill=(255, 255, 255), font=self.font_small)

        return pil_img
    
    def draw_spine_cobb(self, image, result) -> Image.Image:
        spine_points = result["spine_points"]
        labels = result["labels"]
        angles = result["angles"]
        cobb = result["cobb_angle"]
        level = result["level"]

        vis = np.array(image).copy()
        vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)

        # 脊柱折线
        for i in range(len(spine_points) - 1):
            p1 = spine_points[i]
            p2 = spine_points[i + 1]
            cv2.line(
                vis_bgr,
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                (255, 255, 0),
                2,
                cv2.LINE_AA
            )

        # 关键点 + 标签
        for (x, y), lab in zip(spine_points, labels):
            cv2.circle(vis_bgr, (int(x), int(y)), 6, (0, 255, 255), -1, cv2.LINE_AA)
            cv2.putText(
                vis_bgr,
                lab,
                (int(x) + 5, int(y) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA
            )

        # 最大弯曲段高亮
        if len(angles) > 0:
            max_i = int(np.argmax(angles))
            p1 = spine_points[max_i]
            p2 = spine_points[max_i + 1]
            p3 = spine_points[max_i + 2]
            cv2.line(vis_bgr, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 255), 4)
            cv2.line(vis_bgr, (int(p2[0]), int(p2[1])), (int(p3[0]), int(p3[1])), (0, 255, 255), 4)
            cv2.putText(
                vis_bgr,
                f"{cobb:.1f}",
                (int(p2[0]) + 10, int(p2[1])),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
                cv2.LINE_AA
            )

        # PIL文字
        vis_rgb = cv2.cvtColor(vis_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        draw = ImageDraw.Draw(pil_img)

        txt1 = f"Cobb角: {cobb:.1f}°"
        txt2 = f"脊柱侧弯: {level}"
        draw.text((10, 10), txt1, fill=(255, 255, 255), font=self.font)
        draw.text((10, 50), txt2, fill=(255, 255, 255), font=self.font_small)

        return pil_img