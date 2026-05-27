from fastapi import APIRouter, UploadFile, File
from PIL import Image
import numpy as np
import io

from app.services.inference import run_pose
from app.services.multi_view_analysis import MultiViewAnalysis

router = APIRouter()

analyzer = MultiViewAnalysis()

def _to_builtin(value):
    """
    把 numpy / torch / Python 数值递归转换为 JSON 安全类型。
    重点处理 NaN、inf、-inf，避免 FastAPI 返回时报：
    ValueError: Out of range float values are not JSON compliant
    """
    # numpy 数组
    if isinstance(value, np.ndarray):
        return [_to_builtin(v) for v in value.tolist()]
    # numpy 浮点数
    if isinstance(value, np.floating):
        value = float(value)
        return value if np.isfinite(value) else None
    # numpy 整数
    if isinstance(value, np.integer):
        return int(value)
    # Python float，包括 nan / inf
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    # Python int
    if isinstance(value, int):
        return value
    # dict
    if isinstance(value, dict):
        return {str(k): _to_builtin(v) for k, v in value.items()}
    # list / tuple
    if isinstance(value, (list, tuple)):
        return [_to_builtin(v) for v in value]
    return value


def _extract_pose_data(pose_result):
    """从 run_pose 返回结果中提取第一个人体的 keypoints 和 scores。"""
    if not pose_result:
        return None, None, 0.0

    primary = pose_result[0]
    keypoints = np.asarray(primary.get("keypoints"), dtype=float) if primary.get("keypoints") is not None else None
    if keypoints is not None:
        keypoints = np.nan_to_num(
            keypoints,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

    raw_scores = primary.get("scores")
    if raw_scores is None and keypoints is not None and keypoints.ndim == 2 and keypoints.shape[1] >= 3:
        raw_scores = keypoints[:, 2]
    scores = np.asarray(raw_scores, dtype=float) if raw_scores is not None else None

    if scores is not None:
        scores = np.nan_to_num(
            scores,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

    # 不同模型字段名可能不同，尽量兼容。
    detection_score = primary.get("score", primary.get("detection_score", primary.get("bbox_score", 0.0)))
    try:
        detection_score = float(detection_score)
    except Exception:
        detection_score = 0.0

    return keypoints, scores, detection_score

@router.post("/analyze")
async def analyze_posture_api(
    file_front: UploadFile = File(...),
    file_back: UploadFile = File(...),
    file_left: UploadFile = File(...),
    file_right: UploadFile = File(...)
):
    """
    多视图体态估计 API
    接收 4 个视角的图像，进行体态分析
    """
    try:
        # 读取上传的文件
        front_data = await file_front.read()
        back_data = await file_back.read()
        left_data = await file_left.read()
        right_data = await file_right.read()

        # 转换为 PIL 图像
        front_img = Image.open(io.BytesIO(front_data)).convert("RGB")
        back_img = Image.open(io.BytesIO(back_data)).convert("RGB")
        left_img = Image.open(io.BytesIO(left_data)).convert("RGB")
        right_img = Image.open(io.BytesIO(right_data)).convert("RGB")

        # 运行姿态检测并同时提取 keypoints 与 scores
        front_pose_result = run_pose(front_img)
        front_kp, front_scores, front_det_score = _extract_pose_data(front_pose_result)

        back_pose_result = run_pose(back_img)
        back_kp, back_scores, back_det_score = _extract_pose_data(back_pose_result)

        left_pose_result = run_pose(left_img)
        left_kp, left_scores, left_det_score = _extract_pose_data(left_pose_result)

        right_pose_result = run_pose(right_img)
        right_kp, right_scores, right_det_score = _extract_pose_data(right_pose_result)

        detected_views = {
            "front": front_kp is not None,
            "back": back_kp is not None,
            "left": left_kp is not None,
            "right": right_kp is not None,
        }
        detected_count = sum(detected_views.values())

        # 多视图分析
        analysis_result = analyzer.analyze(
            front_kp=front_kp,
            back_kp=back_kp,
            left_kp=left_kp,
            right_kp=right_kp,
            front_scores=front_scores,
            back_scores=back_scores,
            left_scores=left_scores,
            right_scores=right_scores,
        )

        valid_det_scores = [
            float(score)
            for score in [front_det_score, back_det_score, left_det_score, right_det_score]
            if isinstance(score, (int, float, np.integer, np.floating))
            and np.isfinite(float(score))
            and float(score) > 0
        ]

        avg_detection_score = float(np.mean(valid_det_scores)) if valid_det_scores else 0.0

        response_data = {
            "success": detected_count > 0,
            "person_count": int(detected_count),
            "detected_views": detected_views,
            "primary_result": {
                "person_index": 0,
                "detection_score": float(avg_detection_score),
                "summary": {
                    "front_analysis": analysis_result.get("front", {}),
                    "back_analysis": analysis_result.get("back", {}),
                    "left_analysis": analysis_result.get("left", {}),
                    "right_analysis": analysis_result.get("right", {}),
                    "merged_analysis": analysis_result.get("merged", {}),
                    "available_metrics": analysis_result.get("merged", {}).get("metric_type_count", 17),
                }
            },
            "all_results": [
                {
                    "person_index": 0,
                    "detection_score": float(avg_detection_score),
                    "summary": analysis_result.get("merged", {})
                }
            ],
            "analysis_result": analysis_result
        }
        return _to_builtin(response_data)

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "person_count": 0,
            "primary_result": None,
            "all_results": []
        }
