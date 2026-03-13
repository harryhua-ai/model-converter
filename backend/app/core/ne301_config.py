"""NE301 配置生成工具（基于 AIToolStack）

参考：camthink-ai/AIToolStack/backend/utils/ne301_export.py

功能：
- 从 TFLite 模型自动提取量化参数
- 动态计算内存池大小
- 生成完整的 NE301 JSON 配置
"""
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def _convert_to_json_serializable(obj: Any) -> Any:
    """递归转换 NumPy 类型为 Python 原生类型

    处理 NumPy 的 scalar、ndarray 等类型，确保 JSON 序列化成功

    Args:
        obj: 任意 Python 对象

    Returns:
        JSON 可序列化的 Python 对象
    """
    import numpy as np

    if isinstance(obj, dict):
        return {key: _convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        try:
            return int(obj.item())
        except (ValueError, OverflowError, AttributeError):
            return int(obj)
    elif isinstance(obj, np.floating):
        try:
            return float(obj.item())
        except (ValueError, OverflowError, AttributeError):
            return float(obj)
    elif isinstance(obj, np.bool_):
        try:
            return bool(obj.item())
        except (ValueError, OverflowError, AttributeError):
            return bool(obj)
    else:
        return obj


def extract_tflite_quantization_params(
    tflite_path: Path
) -> Tuple[Optional[float], Optional[int], Optional[Tuple[int, int, int]]]:
    """从 TFLite 模型自动提取量化参数

    参考 AIToolStack 的实现，使用 TensorFlow Lite Interpreter 读取模型详情

    Args:
        tflite_path: TFLite 模型文件路径

    Returns:
        (output_scale, output_zero_point, output_shape)
        失败时返回 (None, None, None)
    """
    try:
        import tensorflow as tf

        logger.info(f"正在从 TFLite 模型提取量化参数: {tflite_path}")

        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()

        output_details = interpreter.get_output_details()[0]
        quant_params = output_details['quantization_parameters']

        # 提取 scale 和 zero_point
        scales = quant_params['scales']
        zero_points = quant_params['zero_points']

        output_scale = None
        output_zero_point = None

        if len(scales) > 0 and len(zero_points) > 0:
            output_scale = _convert_to_json_serializable(scales[0])
            output_zero_point = _convert_to_json_serializable(zero_points[0])
            logger.info(f"✅ 提取量化参数: scale={output_scale}, zero_point={output_zero_point}")

        # 提取 output_shape
        output_shape = tuple(_convert_to_json_serializable(output_details['shape']))
        logger.info(f"✅ 提取输出形状: {output_shape}")

        return output_scale, output_zero_point, output_shape

    except Exception as e:
        logger.error(f"❌ 提取量化参数失败: {e}")
        return None, None, None


def calculate_total_boxes(input_size: int) -> int:
    """根据输入尺寸计算 YOLOv8 输出框数量

    YOLOv8 使用 3 个检测头，stride 分别为 8、16、32
    total_boxes = 3 * (H/8 * W/8 + H/16 * W/16 + H/32 * W/32)

    参考 AIToolStack 的精确计算公式

    Args:
        input_size: 输入尺寸（正方形）

    Returns:
        总输出框数量
    """
    if input_size == 256:
        return 1344
    elif input_size == 320:
        return 2100
    elif input_size == 416:
        return 3549
    elif input_size == 480:
        return 4725
    elif input_size == 640:
        return 8400
    else:
        # 通用公式
        scale = input_size // 8
        return 3 * (scale * scale + (scale // 2) ** 2 + (scale // 4) ** 2)


def calculate_memory_pools(
    model_file_size: int,
    input_size: int,
    total_boxes: int,
    output_height: int = 84
) -> Tuple[int, int]:
    """根据模型大小动态计算内存池

    参考 AIToolStack 的智能内存分配策略

    Args:
        model_file_size: 模型文件大小（字节）
        input_size: 输入尺寸
        total_boxes: 总输出框数量
        output_height: 输出高度（YOLOv8 默认 84）

    Returns:
        (exec_memory_pool, ext_memory_pool)
    """
    input_buffer_size = input_size * input_size * 3
    output_buffer_size = total_boxes * output_height

    # exec_memory_pool: 3x 模型大小 + 缓冲区 + 50MB 开销
    exec_memory_pool = max(
        1073741824,  # 最小 1GB
        int(model_file_size * 3 + input_buffer_size + output_buffer_size + 50 * 1024 * 1024)
    )
    exec_memory_pool = min(exec_memory_pool, 2147483648)  # 上限 2GB

    # ext_memory_pool: 5x 模型大小 + 缓冲区 + 100MB 开销
    ext_memory_pool = max(
        2147483648,  # 最小 2GB
        int(model_file_size * 5 + input_buffer_size * 2 + output_buffer_size * 2 + 100 * 1024 * 1024)
    )
    ext_memory_pool = min(ext_memory_pool, 4294967296)  # 上限 4GB

    logger.info(f"计算内存池: exec={exec_memory_pool / 1024 / 1024:.1f}MB, ext={ext_memory_pool / 1024 / 1024:.1f}MB")
    return exec_memory_pool, ext_memory_pool


def generate_ne301_json_config(
    tflite_path: Path,
    model_name: str,
    input_size: int,
    num_classes: int,
    class_names: List[str],
    output_scale: Optional[float] = None,
    output_zero_point: Optional[int] = None,
    confidence_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    max_detections: int = 300,
    total_boxes: Optional[int] = None,
    output_shape: Optional[Tuple[int, int, int]] = None,
    alignment_requirement: int = 8,
) -> Dict[str, Any]:
    """生成完整的 NE301 JSON 配置

    参考 AIToolStack 的完整配置结构，包含所有必需字段

    Args:
        tflite_path: TFLite 模型路径
        model_name: 模型名称
        input_size: 输入尺寸
        num_classes: 类别数量
        class_names: 类别名称列表
        output_scale: 量化缩放因子（可选，自动提取）
        output_zero_point: 量化零点（可选，自动提取）
        confidence_threshold: 置信度阈值
        iou_threshold: IoU 阈值
        max_detections: 最大检测数
        total_boxes: 总输出框数（可选，自动计算）
        output_shape: 输出形状（可选，自动提取）
        alignment_requirement: 内存对齐要求

    Returns:
        完整的 NE301 JSON 配置字典
    """
    logger.info(f"生成 NE301 JSON 配置: {model_name}")

    # 1. 尝试从 TFLite 模型提取参数
    if output_scale is None or output_zero_point is None or output_shape is None:
        extracted_scale, extracted_zero_point, extracted_shape = extract_tflite_quantization_params(tflite_path)

        if extracted_scale is not None:
            output_scale = extracted_scale
        if extracted_zero_point is not None:
            output_zero_point = extracted_zero_point
        if extracted_shape is not None:
            output_shape = extracted_shape

    # 2. 使用默认值（如果提取失败）
    if output_scale is None:
        output_scale = 0.003921568859368563  # 1/255 (uint8→int8)
        logger.warning(f"⚠️  使用默认 output_scale: {output_scale}")

    if output_zero_point is None:
        output_zero_point = -128  # int8 零点
        logger.warning(f"⚠️  使用默认 output_zero_point: {output_zero_point}")

    # 3. 计算 total_boxes（如果未提供）
    if total_boxes is None:
        total_boxes = calculate_total_boxes(input_size)
        logger.info(f"✅ 计算 total_boxes: {total_boxes}")

    # 4. 确定输出维度
    if output_shape is None:
        output_shape = (1, 84, total_boxes)  # 默认 YOLOv8 输出形状
        logger.warning(f"⚠️  使用默认 output_shape: {output_shape}")

    batch, output_height, width = output_shape

    # 5. 计算内存池
    model_file_size = tflite_path.stat().st_size
    exec_memory_pool, ext_memory_pool = calculate_memory_pools(
        model_file_size, input_size, total_boxes, output_height
    )

    # 6. 生成完整配置
    config = {
        "version": "1.0.0",
        "model_info": {
            "name": model_name,
            "type": "OBJECT_DETECTION",
            "framework": "TFLITE",
            "format": "INT8",
            "input_size": input_size,
            "num_classes": num_classes
        },
        "input_spec": {
            "width": input_size,
            "height": input_size,
            "channels": 3,
            "data_type": "uint8",
            "color_format": "RGB888_YUV444_1",
            "normalization": {
                "scale": 255.0,
                "offset": 0.0
            }
        },
        "output_spec": {
            "num_outputs": 1,
            "outputs": [{
                "name": "output0",
                "batch": int(batch),
                "height": int(output_height),
                "width": int(width),
                "channels": 1,
                "data_type": "int8",
                "scale": float(output_scale),
                "zero_point": int(output_zero_point)
            }]
        },
        "memory": {
            "exec_memory_pool": int(exec_memory_pool),
            "ext_memory_pool": int(ext_memory_pool),
            "alignment_requirement": int(alignment_requirement)
        },
        "postprocess_type": "pp_od_yolo_v8_ui",
        "postprocess_params": {
            "num_classes": int(num_classes),
            "class_names": class_names,
            "total_boxes": int(total_boxes),
            "confidence_threshold": float(confidence_threshold),
            "iou_threshold": float(iou_threshold),
            "max_detections": int(max_detections)
        }
    }

    # ✅ 调试日志
    import json
    config_size = len(json.dumps(config, indent=2))
    logger.info(f"✅ NE301 JSON 配置生成完成（大小: {config_size} 字节）")

    if config_size < 1000:
        logger.warning(f"⚠️  配置大小异常，完整配置:\n{json.dumps(config, indent=2)}")
    else:
        logger.debug(f"JSON 配置预览: {json.dumps(config, indent=2)[:500]}...")

    return config
