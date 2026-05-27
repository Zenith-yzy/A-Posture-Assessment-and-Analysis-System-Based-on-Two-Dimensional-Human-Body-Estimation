from PIL import Image
import torch
from app.models.pose_model import pose_model, device


def run_pose(image: Image.Image):
    image = image.convert("RGB")
    # stage 1: 人体检测
    processor = pose_model.det_processor
    model = pose_model.det_model

    inputs = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    results = processor.post_process_object_detection(
        outputs, target_sizes=torch.tensor([(image.height, image.width)]).to(device), threshold=0.3
    )

    result = results[0]

    # 只保留人体类别，COCO 中 person label = 0
    person_boxes = result["boxes"][result["labels"] == 0]

    if person_boxes.shape[0] == 0:
        return []

    # 转到 CPU + numpy
    person_boxes = person_boxes.detach().cpu().numpy()

    # VOC 格式: x1, y1, x2, y2
    # 转 COCO 格式: x1, y1, w, h
    person_boxes[:, 2] = person_boxes[:, 2] - person_boxes[:, 0]
    person_boxes[:, 3] = person_boxes[:, 3] - person_boxes[:, 1]

    pose_processor = pose_model.pose_processor
    pose_net = pose_model.pose_model

    pose_inputs = pose_processor(
        image,
        boxes=[person_boxes],
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        pose_outputs = pose_net(**pose_inputs)

    pose_results = pose_processor.post_process_pose_estimation(
        pose_outputs,
        boxes=[person_boxes]
    )

    # pose_results[0] 表示当前图片中的所有人体姿态结果
    return pose_results[0]
