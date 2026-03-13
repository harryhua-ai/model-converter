"""
Pytest 配置文件
提供测试固件和测试工具
"""
import os
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def sample_config_dict():
    """示例转换配置字典"""
    return {
        "model_name": "test_model",
        "model_type": "YOLOv8",
        "model_version": "1.0.0",
        "input_width": 480,
        "input_height": 480,
        "input_data_type": "uint8",
        "color_format": "RGB888_YUV444_1",
        "quantization_type": "int8",
        "quantization_mode": "per_channel",
        "postprocess_type": "pp_od_yolo_v8_ui",
        "num_classes": 80,
        "class_names": [],
        "confidence_threshold": 0.25,
        "iou_threshold": 0.45,
        "max_detections": 100,
        "total_boxes": 4800,
        "mean": [0.0, 0.0, 0.0],
        "std": [255.0, 255.0, 255.0],
        "use_custom_calibration": False,
        "calibration_dataset_filename": None,
    }


@pytest.fixture
def sample_config(sample_config_dict):
    """示例转换配置对象"""
    from app.models.schemas import ConversionConfig
    return ConversionConfig(**sample_config_dict)


@pytest.fixture
def client():
    """创建测试客户端"""
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)
