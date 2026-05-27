from app.services.posture_analysis import PostureAnalysis


class MultiViewAnalysis:
    """多视图体态分析类"""
    def __init__(self):
        self.analyzer = PostureAnalysis()

    def analyze(
        self,
        front_kp=None,
        back_kp=None,
        left_kp=None,
        right_kp=None,
        front_scores=None,
        back_scores=None,
        left_scores=None,
        right_scores=None,
    ):
        """分析多视图关键点数据。"""
        results = {
            "front": self.analyze_front(front_kp, front_scores) if front_kp is not None else {},
            "back": self.analyze_back(back_kp, back_scores) if back_kp is not None else {},
            "left": self.analyze_side(left_kp, left_scores, view_name="left") if left_kp is not None else {},
            "right": self.analyze_side(right_kp, right_scores, view_name="right") if right_kp is not None else {},
        }
        results["merged"] = self.analyze_merged(results)
        return results

    def _safe_call(self, func, *args, **kwargs):
        """单项指标独立计算，避免一个指标失败导致整个视角失败。"""
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            return {
                "type": getattr(func, "__name__", "unknown"),
                "level": "无法计算",
                "error": str(exc),
            }

    def _attach_view_score(self, results):
        results["posture_score"] = self._score_view(results)
        return results

    def analyze_front(self, front_kp, front_scores=None):
        """正面视图：主要分析对称性、头/骨盆侧倾、下肢与足部姿态。"""
        results = {
            "shoulder_asymmetry": self._safe_call(self.analyzer.analyze_shoulder_asymmetry, front_kp),
            "pelvic_tilt": self._safe_call(self.analyzer.analyze_pelvic_tilt, front_kp),
            "head_tilt": self._safe_call(self.analyzer.analyze_head_tilt, front_kp),
            "head_rotation": self._safe_call(self.analyzer.analyze_head_rotation, front_kp, front_scores),
            "pelvic_rotation": self._safe_call(self.analyzer.analyze_pelvic_rotation, front_kp, front_scores),
            "leg_length_asymmetry": self._safe_call(self.analyzer.analyze_leg_length_asymmetry, front_kp),
            "foot_progression_angle": self._safe_call(self.analyzer.analyze_fpa, front_kp),
            "ankle_inversion": self._safe_call(self.analyzer.analyze_ankle_inversion, front_kp),
            "knee_valgus_varus": self._safe_call(self.analyzer.analyze_knee_valgus_varus, front_kp),
            "center_shift": self._safe_call(self.analyzer.analyze_center_shift, front_kp),
        }
        return self._attach_view_score(results)

    def analyze_back(self, back_kp, back_scores=None):
        """背面视图：主要分析脊柱侧弯风险，也可复核肩/骨盆水平。"""
        results = {
            "spine_cobb": self._safe_call(self.analyzer.analyze_spine_cobb, back_kp),
            "shoulder_asymmetry": self._safe_call(self.analyzer.analyze_shoulder_asymmetry, back_kp),
            "pelvic_tilt": self._safe_call(self.analyzer.analyze_pelvic_tilt, back_kp),
        }
        return self._attach_view_score(results)

    def analyze_side(self, side_kp, side_scores=None, view_name="side"):
        """侧面视图：主要分析头前伸、圆肩、胸/腰曲度、骨盆前后倾、膝超伸。"""
        results = {
            "head_forward": self._safe_call(self.analyzer.analyze_head_forward, side_kp),
            "round_shoulder": self._safe_call(self.analyzer.analyze_round_shoulder, side_kp),
            "thoracic_kyphosis": self._safe_call(self.analyzer.analyze_thoracic_kyphosis, side_kp),
            "pelvic_anterior_posterior_tilt": self._safe_call(self.analyzer.analyze_pelvic_anterior_posterior_tilt, side_kp),
            "lumbar_lordosis": self._safe_call(self.analyzer.analyze_lumbar_lordosis, side_kp),
            "knee_hyperextension": self._safe_call(self.analyzer.analyze_knee_hyperextension, side_kp),
            "center_shift": self._safe_call(self.analyzer.analyze_center_shift, side_kp),
        }
        return self._attach_view_score(results)

    def _severity(self, metric):
        """把中文等级转换为风险分值：0 正常，1 轻度，2 中度，3 重度。"""
        if not isinstance(metric, dict):
            return None

        level = str(metric.get("level", ""))
        if not level or level in {"无法计算", "无法判断", "异常"}:
            return None
        if "重度" in level or "中重度" in level:
            return 3
        if "中度" in level or "轻中度" in level:
            return 2
        if "轻度" in level:
            return 1
        if "正常" in level or "正中" in level:
            return 0
        return None

    def _iter_metric_results(self, results):
        for view in ["front", "back", "left", "right"]:
            view_result = results.get(view, {})
            if not isinstance(view_result, dict):
                continue
            for metric_name, metric in view_result.items():
                if metric_name == "posture_score":
                    continue
                if isinstance(metric, dict):
                    yield view, metric_name, metric

    def _score_view(self, view_result):
        severities = []
        for key, metric in view_result.items():
            if key == "posture_score":
                continue
            sev = self._severity(metric)
            if sev is not None:
                severities.append(sev)

        if not severities:
            return None

        # 每个指标最高扣 18 分：轻度扣 6、中度扣 12、重度扣 18。
        penalty = sum(severities) * 0.06
        score = max(0.0, min(1.0, 1.0 - penalty))
        return round(score, 4)

    def analyze_merged(self, results):
        """根据所有有效指标动态合并评分，替代固定分数。"""
        view_scores = [
            results.get(view, {}).get("posture_score")
            for view in ["front", "back", "left", "right"]
            if isinstance(results.get(view, {}).get("posture_score"), (int, float))
        ]

        severities = []
        abnormal_items = []
        symmetry_metric_names = {
            "shoulder_asymmetry",
            "pelvic_tilt",
            "head_tilt",
            "leg_length_asymmetry",
            "knee_valgus_varus",
            "ankle_inversion",
            "foot_progression_angle",
        }
        symmetry_severities = []

        for view, metric_name, metric in self._iter_metric_results(results):
            sev = self._severity(metric)
            if sev is None:
                continue
            severities.append(sev)
            if metric_name in symmetry_metric_names:
                symmetry_severities.append(sev)
            if sev > 0:
                abnormal_items.append({
                    "view": view,
                    "metric": metric_name,
                    "level": metric.get("level"),
                    "direction": metric.get("direction") or metric.get("foot_type") or "",
                })

        if view_scores:
            overall = sum(view_scores) / len(view_scores)
        elif severities:
            overall = max(0.0, 1.0 - sum(severities) * 0.06)
        else:
            overall = 0.0

        if symmetry_severities:
            symmetry_score = max(0.0, 1.0 - sum(symmetry_severities) * 0.06)
        else:
            symmetry_score = overall

        # 稳定性主要参考重心偏移、骨盆、膝、足踝相关项目。
        stability_names = {
            "center_shift",
            "pelvic_tilt",
            "pelvic_anterior_posterior_tilt",
            "knee_valgus_varus",
            "knee_hyperextension",
            "ankle_inversion",
            "foot_progression_angle",
        }
        stability_severities = [
            self._severity(metric)
            for _, metric_name, metric in self._iter_metric_results(results)
            if metric_name in stability_names and self._severity(metric) is not None
        ]
        if stability_severities:
            stability_score = max(0.0, 1.0 - sum(stability_severities) * 0.06)
        else:
            stability_score = overall

        if not abnormal_items:
            recommendation = "当前有效指标未发现明显异常，建议继续保持良好站姿，并定期复测。"
        else:
            top_items = abnormal_items[:5]
            desc = "、".join(
                f"{item['view']}:{item['metric']}({item['level']})" for item in top_items
            )
            recommendation = f"检测到 {len(abnormal_items)} 项姿态风险，重点关注：{desc}。建议结合正侧背多视角照片复核，并进行针对性拉伸、力量训练和站姿调整。"

        return {
            "overall_posture_score": round(float(overall), 4),
            "symmetry_score": round(float(symmetry_score), 4),
            "stability_score": round(float(stability_score), 4),
            "metric_type_count": 17,
            "valid_metric_count": int(len(severities)),
            "abnormal_metric_count": int(len(abnormal_items)),
            "abnormal_items": abnormal_items,
            "recommendation": recommendation,
        }


# 为了向后兼容性，创建一个别名
MultiViewPostureAnalysis = MultiViewAnalysis
