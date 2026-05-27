import torch
from transformers import (
    AutoProcessor,
    RTDetrForObjectDetection,
    VitPoseForPoseEstimation,
)

device = "cuda" if torch.cuda.is_available() else "cpu"

class PoseModel:
    """
    人体检测 + SynthPose姿态估计模型加载类
    Stage 1:
        使用 RT-DETR 检测人体框
    Stage 2:
        使用 SynthPose-VitPose 模型估计人体关键点
    """
    def __init__(self):
        # stage 1: 人体检测模型
        self.det_processor = AutoProcessor.from_pretrained(
            "PekingU/rtdetr_r50vd_coco_o365"
        )

        self.det_model = RTDetrForObjectDetection.from_pretrained(
            "PekingU/rtdetr_r50vd_coco_o365"
        ).to(device)

        self.det_model.eval()

        # stage 2: 关键点检测模型
        self.pose_processor = AutoProcessor.from_pretrained(
            "yonigozlan/synthpose-vitpose-base-hf"
        )

        self.pose_model = VitPoseForPoseEstimation.from_pretrained(
            "yonigozlan/synthpose-vitpose-base-hf"
        ).to(device)

        self.pose_model.eval()

pose_model = PoseModel()
