"""
配置预设 API 端点
提供常用的模型配置预设
"""
from fastapi import APIRouter
from app.models.schemas import ConfigPreset, ModelType, PostprocessType, ColorFormat

router = APIRouter()

# 内置配置预设（按优先级排序，第一个为默认）
PRESETS: list[ConfigPreset] = [
    ConfigPreset(
        id="yolov8n-256",
        name="YOLOv8n 256×256（推荐）",
        description="快速检测，适合边缘设备 | 7-10 分钟",
        config={
            "model_name": "yolov8n_256",
            "model_type": ModelType.YOLOV8,
            "model_version": "1.0.0",
            "input_width": 256,
            "input_height": 256,
            "input_data_type": "uint8",
            "color_format": ColorFormat.RGB888_YUV444_1,
            "quantization_type": "int8",
            "quantization_mode": "per_channel",
            "postprocess_type": PostprocessType.PP_OD_YOLO_V8_UI,
            "num_classes": 80,
            "class_names": [],
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_detections": 100,
            "total_boxes": 1344,
            "mean": [0.0, 0.0, 0.0],
            "std": [255.0, 255.0, 255.0],
        },
    ),
    ConfigPreset(
        id="yolov8n-320",
        name="YOLOv8n 320×320",
        description="平衡性能与精度 | 10-15 分钟",
        config={
            "model_name": "yolov8n_320",
            "model_type": ModelType.YOLOV8,
            "model_version": "1.0.0",
            "input_width": 320,
            "input_height": 320,
            "input_data_type": "uint8",
            "color_format": ColorFormat.RGB888_YUV444_1,
            "quantization_type": "int8",
            "quantization_mode": "per_channel",
            "postprocess_type": PostprocessType.PP_OD_YOLO_V8_UI,
            "num_classes": 80,
            "class_names": [],
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_detections": 100,
            "total_boxes": 3200,
            "mean": [0.0, 0.0, 0.0],
            "std": [255.0, 255.0, 255.0],
        },
    ),
    ConfigPreset(
        id="yolov8n-480",
        name="YOLOv8n 480×480",
        description="高精度检测 | 15-20 分钟",
        config={
            "model_name": "yolov8n_480",
            "model_type": ModelType.YOLOV8,
            "model_version": "1.0.0",
            "input_width": 480,
            "input_height": 480,
            "input_data_type": "uint8",
            "color_format": ColorFormat.RGB888_YUV444_1,
            "quantization_type": "int8",
            "quantization_mode": "per_channel",
            "postprocess_type": PostprocessType.PP_OD_YOLO_V8_UI,
            "num_classes": 80,
            "class_names": [],
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_detections": 100,
            "total_boxes": 4800,
            "mean": [0.0, 0.0, 0.0],
            "std": [255.0, 255.0, 255.0],
        },
    ),
    # 注意：已移除 640×640 预设（在 Apple Silicon Rosetta 环境下会卡住）
    # 如需使用更高精度，请选择 480×480 并等待更长时间
    ConfigPreset(
        id="yolox-nano-480",
        name="YOLOX Nano 480x480",
        description="ST 优化的边缘检测模型",
        config={
            "model_name": "yolox_nano_480",
            "model_type": ModelType.YOLOX,
            "model_version": "1.0.0",
            "input_width": 480,
            "input_height": 480,
            "input_data_type": "uint8",
            "color_format": ColorFormat.RGB888_YUV444_1,
            "quantization_type": "int8",
            "quantization_mode": "per_channel",
            "postprocess_type": PostprocessType.PP_OD_ST_YOLOX_UF,
            "num_classes": 80,
            "class_names": [],
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_detections": 100,
            "total_boxes": 4800,
            "mean": [0.0, 0.0, 0.0],
            "std": [255.0, 255.0, 255.0],
        },
    ),
]


@router.get("/", response_model=list[ConfigPreset])
async def get_presets() -> list[ConfigPreset]:
    """
    获取所有配置预设

    Returns:
        list[ConfigPreset]: 配置预设列表
    """
    return PRESETS


@router.get("/{preset_id}", response_model=ConfigPreset)
async def get_preset(preset_id: str) -> ConfigPreset:
    """
    获取指定配置预设

    Args:
        preset_id: 预设 ID

    Returns:
        ConfigPreset: 配置预设

    Raises:
        HTTPException: 预设不存在
    """
    for preset in PRESETS:
        if preset.id == preset_id:
            return preset

    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail=f"预设 {preset_id} 不存在")
