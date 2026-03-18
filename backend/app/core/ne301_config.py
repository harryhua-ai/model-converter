"""
NE301 工具链配置管理

支持版本检测和动态适配，兼容 NE301 工具链的后续更新
参考核心转换逻辑的实现
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# TensorFlow import (可选)
try:
    import tensorflow as tf

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class NE301Version:
    """NE301 版本信息"""

    major: int
    minor: int
    patch: int
    build: int = 0
    suffix: str = ""

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}.{self.build}"
        return f"{base}_{self.suffix}" if self.suffix else base

    @staticmethod
    def parse(version_str: str) -> Optional["NE301Version"]:
        """从字符串解析版本号"""
        # 支持格式: "2.0.0.0", "2.0.0", "2.0.0.0-alpha"
        match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?(?:-([a-zA-Z0-9]+))?", version_str)
        if match:
            major, minor, patch, build, suffix = match.groups()
            return NE301Version(
                major=int(major),
                minor=int(minor),
                patch=int(patch),
                build=int(build) if build else 0,
                suffix=suffix or "",
            )
        return None

    @staticmethod
    def generate_timestamp_version() -> "NE301Version":
        """生成基于时间戳的版本号"""
        # 格式: 2.0.0.BUILD (BUILD 是当天的秒数 % 10000)
        import time

        build = int(time.time()) % 10000
        return NE301Version(major=2, minor=0, patch=0, build=build)

    def to_tuple(self) -> Tuple[int, int, int, int]:
        """转换为元组"""
        return (self.major, self.minor, self.patch, self.build)


@dataclass
class OTAConfig:
    """OTA 打包配置"""

    magic: int = 0x4F544155  # "OTAU"
    header_version: int = 0x0100  # v1.0
    header_size: int = 1024

    # 固件类型映射
    fw_type_map: Dict[str, int] = field(
        default_factory=lambda: {
            "fsbl": 0x01,
            "app": 0x02,
            "web": 0x03,
            "ai_model": 0x04,
            "config": 0x05,
            "patch": 0x06,
            "full": 0x07,
        }
    )


@dataclass
class ModelPackagerConfig:
    """模型打包配置"""

    package_magic: int = 0x314D364E  # "N6M1"
    package_version: int = 0x030000  # v3.0.0

    # 工具路径（相对于 NE301 项目根目录）
    ota_packer_script: str = "Script/ota_packer.py"
    model_packager_script: str = "Script/model_packager.py"
    version_header_script: str = "Script/version_header.py"

    # Makefile 目标
    model_make_target: str = "model"

    # 版本配置
    model_version_template: str = "{major}.{minor}.{patch}.{build}"
    default_major_version: int = 2
    default_minor_version: int = 0
    default_patch_version: int = 0


@dataclass
class NE301Toolchain:
    """NE301 工具链信息"""

    project_root: Path
    version: Optional[NE301Version] = None
    config: ModelPackagerConfig = field(default_factory=ModelPackagerConfig)

    # 检测到的工具和脚本
    available_tools: Dict[str, bool] = field(default_factory=dict)
    tool_versions: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """初始化时检测工具链"""
        self._detect_toolchain()

    def _detect_toolchain(self) -> None:
        """检测 NE301 工具链版本和可用工具"""
        logger.info("🔍 检测 NE301 工具链...")

        # 检测版本文件
        version_mk = self.project_root / "version.mk"
        if version_mk.exists():
            self._parse_version_mk(version_mk)

        # 检测可用的打包工具
        self._detect_tools()

        # 记录检测结果
        self._log_detection_results()

    def _parse_version_mk(self, version_mk_path: Path) -> None:
        """解析 version.mk 文件"""
        try:
            content = version_mk_path.read_text()

            # 解析主版本号
            major = self._extract_version_var(content, "VERSION_MAJOR", 2)
            minor = self._extract_version_var(content, "VERSION_MINOR", 0)
            patch = self._extract_version_var(content, "VERSION_PATCH", 0)
            build = self._extract_version_var(content, "VERSION_BUILD", 0)

            # ✅ 修复：允许 minor 和 patch 为 0
            if major is not None and minor is not None and patch is not None:
                self.version = NE301Version(
                    major=major, minor=minor, patch=patch, build=build if build is not None else 0
                )
                logger.info(f"✓ 检测到 NE301 版本: {self.version}")

        except Exception as e:
            logger.warning(f"⚠️  无法解析版本文件: {e}")

    def _extract_version_var(self, content: str, var_name: str, default: int) -> Optional[int]:
        """从 Makefile 内容中提取版本变量"""
        # 匹配: VERSION_MAJOR ?= 2 或 VERSION_MAJOR := 2
        match = re.search(rf"{var_name}\s*:?=\s*(\d+)", content)
        return int(match.group(1)) if match else default

    def _detect_tools(self) -> None:
        """检测可用的打包工具"""
        tools_to_check = {
            "ota_packer": self.project_root / self.config.ota_packer_script,
            "model_packager": self.project_root / self.config.model_packager_script,
            "version_header": self.project_root / self.config.version_header_script,
        }

        for tool_name, tool_path in tools_to_check.items():
            exists = tool_path.exists()
            self.available_tools[tool_name] = exists

            if exists:
                logger.info(f"✓ 找到工具: {tool_name}")

                # 尝试获取工具版本
                version = self._get_tool_version(tool_path)
                if version:
                    self.tool_versions[tool_name] = version
                    logger.info(f"  版本: {version}")

    def _get_tool_version(self, script_path: Path) -> Optional[str]:
        """获取脚本的版本信息"""
        try:
            content = script_path.read_text()

            # 查找版本号注释
            # 例如: # Version: 1.0 或 VERSION = "1.0"
            version_matches = [
                re.search(r"#\s*Version:\s*([\d.]+)", content),
                re.search(r'VE?RSION\s*=\s*["\']([\d.]+)["\']', content),
            ]

            for match in version_matches:
                if match:
                    return match.group(1)

        except Exception:
            pass

        return None

    def _log_detection_results(self) -> None:
        """记录检测结果摘要"""
        logger.info("=" * 50)
        logger.info("NE301 工具链检测结果:")
        logger.info(f"  项目路径: {self.project_root}")
        logger.info(f"  版本: {self.version or '未知'}")
        logger.info(f"  可用工具:")
        for tool_name, available in self.available_tools.items():
            status = "✓" if available else "✗"
            version = (
                f" ({self.tool_versions.get(tool_name)})" if tool_name in self.tool_versions else ""
            )
            logger.info(f"    {status} {tool_name}{version}")
        logger.info("=" * 50)

    def get_ota_packager(self) -> Optional[Path]:
        """获取 OTA 打包工具路径"""
        tool_name = "ota_packer"
        if self.available_tools.get(tool_name):
            return self.project_root / self.config.ota_packer_script
        return None

    def get_model_packager(self) -> Optional[Path]:
        """获取模型打包工具路径"""
        tool_name = "model_packager"
        if self.available_tools.get(tool_name):
            return self.project_root / self.config.model_packager_script
        return None

    def get_model_version(self) -> NE301Version:
        """获取模型版本号（从 version.mk 读取）

        动态读取 version.mk 中的 MODEL_VERSION_OVERRIDE，确保与 OTA packer 一致
        如果 MODEL_VERSION_OVERRIDE 未定义，则使用主版本号
        """
        version_mk = self.project_root / "version.mk"

        if not version_mk.exists():
            logger.warning(f"⚠️  version.mk 不存在，使用默认版本 3.0.0.1")
            return NE301Version(3, 0, 0, 1)

        try:
            with open(version_mk, "r") as f:
                content = f.read()

            # ✅ 优先读取 MODEL_VERSION_OVERRIDE（如果定义）
            model_version_match = re.search(
                r"MODEL_VERSION_OVERRIDE\s*:?=\s*(\d+\.\d+\.\d+\.\d+)", content
            )

            if model_version_match:
                # 使用 MODEL_VERSION_OVERRIDE
                version_str = model_version_match.group(1)
                parts = version_str.split(".")

                if len(parts) == 4:
                    major, minor, patch, build = map(int, parts)
                    version = NE301Version(major, minor, patch, build)
                    logger.info(f"✅ 从 version.mk 读取 MODEL_VERSION_OVERRIDE: {version}")
                    return version

            # ✅ 回退：读取主版本号
            logger.info("MODEL_VERSION_OVERRIDE 未定义，使用主版本号")
            major = self._extract_version_var(content, "VERSION_MAJOR", 3)
            minor = self._extract_version_var(content, "VERSION_MINOR", 0)
            patch = self._extract_version_var(content, "VERSION_PATCH", 0)
            build = self._extract_version_var(content, "VERSION_BUILD", 1)

            version = NE301Version(major, minor, patch, build)
            logger.info(f"✅ 从 version.mk 读取主版本号: {version}")
            return version

        except Exception as e:
            logger.warning(f"⚠️  读取 version.mk 失败: {e}，使用默认版本")
            return NE301Version(3, 0, 0, 1)

    def supports_ota_package(self) -> bool:
        """检查是否支持 OTA 打包"""
        return self.available_tools.get("ota_packer", False)

    def supports_model_package(self) -> bool:
        """检查是否支持模型打包"""
        return self.available_tools.get("model_packager", False)

    def get_best_packaging_method(self) -> str:
        """
        获取最佳的打包方式

        Returns:
            'ota': OTA 打包（推荐，兼容设备升级）
            'model': 纯模型打包（备用）
            'fallback': 降级到 TFLite
        """
        if self.supports_ota_package():
            return "ota"
        elif self.supports_model_package():
            return "model"
        else:
            return "fallback"

    def get_package_name(self, task_id: str, packaging_method: str) -> str:
        """
        生成打包文件名

        Args:
            task_id: 任务 ID
            packaging_method: 打包方式 ('ota', 'model', 'fallback')

        Returns:
            文件名（不含扩展名）
        """
        version = self.get_model_version()

        if packaging_method == "ota":
            # OTA 固件: ne301_Model_v2.0.0.12345_pkg.bin
            return f"ne301_Model_v{version}_pkg"
        elif packaging_method == "model":
            # 模型包: ne301_Model_v2.0.0.12345.bin
            return f"ne301_Model_v{version}"
        else:
            # 降级: quantized_model_taskId.tflite
            return f"quantized_model_{task_id}"

    def get_extension(self, packaging_method: str) -> str:
        """获取文件扩展名"""
        if packaging_method in ("ota", "model"):
            return ".bin"
        else:
            return ".tflite"


class NE301ConfigManager:
    """NE301 配置管理器（单例）"""

    _instance: Optional["NE301ConfigManager"] = None
    _cache: Dict[Path, NE301Toolchain] = {}

    @classmethod
    def get_toolchain(cls, ne301_project_path: Path) -> NE301Toolchain:
        """
        获取 NE301 工具链实例（带缓存）

        Args:
            ne301_project_path: NE301 项目路径

        Returns:
            NE301Toolchain 实例
        """
        # 规范化路径
        ne301_project_path = ne301_project_path.resolve()

        # 检查缓存
        if ne301_project_path in cls._cache:
            return cls._cache[ne301_project_path]

        # 创建新实例
        toolchain = NE301Toolchain(project_root=ne301_project_path)
        cls._cache[ne301_project_path] = toolchain
        return toolchain

    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._cache.clear()


def get_ne301_toolchain(ne301_project_path: Path) -> NE301Toolchain:
    """便捷函数：获取 NE301 工具链实例"""
    return NE301ConfigManager.get_toolchain(ne301_project_path)


def extract_tflite_quantization_params(
    tflite_path: Path,
) -> Tuple[Optional[float], Optional[int], Optional[Tuple[int, int, int]], Optional[Dict]]:
    """
    从 TFLite 模型中提取量化参数、输出维度及详细信息

    Args:
        tflite_path: TFLite 模型文件路径

    Returns:
        Tuple of (output_scale, output_zero_point, output_shape, input_details_dict)
        All return values are converted to Python native types (JSON serializable)
    """
    if not TENSORFLOW_AVAILABLE:
        logger.warning(
            "TensorFlow not available, cannot extract quantization parameters from TFLite model"
        )
        return None, None, None, None

    try:
        # Load TFLite model
        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()

        # Get input details (for data type and shape validation)
        input_details = interpreter.get_input_details()[0]
        input_info = {
            "dtype": str(input_details["dtype"].__name__),
            "shape": [int(x) for x in input_details["shape"]],
        }

        # Get output tensor details
        output_details = interpreter.get_output_details()[0]  # Assume only one output
        output_shape = output_details["shape"]  # e.g., [1, 84, 1344]

        # Convert output_shape to Python native types (handle NumPy int64/int32)
        if output_shape is not None:
            output_shape = tuple(int(x) for x in output_shape)

        # Extract quantization parameters
        output_scale = None
        output_zero_point = None

        if "quantization_parameters" in output_details:
            quant_params = output_details["quantization_parameters"]

            if quant_params.get("scales") and len(quant_params["scales"]) > 0:
                output_scale = float(quant_params["scales"][0])

            if quant_params.get("zero_points") and len(quant_params["zero_points"]) > 0:
                output_zero_point = int(quant_params["zero_points"][0])

        logger.info(
            f"✅ 从 TFLite 模型提取参数: scale={output_scale}, zp={output_zero_point}, out_shape={output_shape}, in_dtype={input_info['dtype']}"
        )
        return output_scale, output_zero_point, output_shape, input_info

    except Exception as e:
        logger.warning(f"从 TFLite 模型提取参数失败: {e}", exc_info=True)
        return None, None, None, None


def generate_ne301_json_config(
    tflite_path: Path,
    model_name: str,
    input_size: int,
    num_classes: int,
    class_names: List[str],
    confidence_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    max_detections: int = 100,
    total_boxes: Optional[int] = None,
    postprocess_type: Optional[str] = None,
    norm_mean: Optional[List[float]] = None,
    norm_std: Optional[List[float]] = None,
) -> Dict:
    """
    生成 NE301 模型 JSON 配置

    参考转换引擎的实现，自动从 TFLite 模型提取量化参数

    Args:
        tflite_path: TFLite 模型文件路径
        model_name: 模型名称
        input_size: 输入尺寸
        num_classes: 类别数量
        class_names: 类别名称列表
        confidence_threshold: 置信度阈值
        iou_threshold: IoU 阈值
        max_detections: 最大检测数
        total_boxes: 总框数
        postprocess_type: 后处理类型 (e.g., 'pp_od_yolo_v8_ui')，如果为 None 则根据类型自动推断
    """
    # ⭐ 关键修复：从 TFLite 模型自动提取量化参数、输出形状和输入信息
    # 修复解包: extract_tflite_quantization_params 现在返回 4 个值
    output_scale, output_zero_point, output_shape, input_info = extract_tflite_quantization_params(
        tflite_path
    )

    # 使用默认值（如果提取失败）
    output_scale = output_scale if output_scale is not None else 1.0
    output_zero_point = output_zero_point if output_zero_point is not None else 0
    input_dtype = input_info.get("dtype", "uint8") if input_info else "uint8"

    # 从输出形状提取高度和宽度
    if output_shape is not None:
        output_height = output_shape[1] if len(output_shape) > 1 else (4 + num_classes)
        if total_boxes is None:
            total_boxes = output_shape[2] if len(output_shape) > 2 else 1344
    else:
        output_height = 4 + num_classes
        total_boxes = total_boxes or 1344

    # 自动推断后处理类型
    if postprocess_type is None:
        if input_dtype.lower() in ("uint8", "uint8_t"):
            postprocess_type = "pp_od_yolo_v8_ui"
        else:
            postprocess_type = "pp_od_yolo_v8_uf"

    # 归一化参数逻辑 (uint8 常用 [0, 255])
    norm_enabled = True
    mean = norm_mean if norm_mean is not None else [0.0, 0.0, 0.0]
    std = norm_std if norm_std is not None else [255.0, 255.0, 255.0]

    logger.info(
        f"📋 生成 JSON 配置: output_scale={output_scale}, output_zero_point={output_zero_point}, "
        f"output_height={output_height}, total_boxes={total_boxes}, in_dtype={input_dtype}, pp={postprocess_type}"
    )

    return {
        "version": "1.0.0",
        "model_info": {
            "name": model_name,
            "version": "1.0.0",
            "description": f"{model_name} - YOLOv8 Object Detection",
            "type": "OBJECT_DETECTION",
            "framework": "TFLITE",
            "author": "CamThink",
        },
        "input_spec": {
            "width": input_size,
            "height": input_size,
            "channels": 3,
            "data_type": "uint8" if "uint8" in input_dtype.lower() else "float32",
            "color_format": "RGB888_YUV444_1",
            "normalization": {"enabled": norm_enabled, "mean": mean, "std": std},
        },
        "output_spec": {
            "num_outputs": 1,
            "outputs": [
                {
                    "name": "output0",
                    "batch": 1,
                    "height": output_height,
                    "width": total_boxes,
                    "channels": 1,
                    "data_type": (
                        "int8" if output_zero_point != 0 or output_scale != 1.0 else "float32"
                    ),
                    "scale": output_scale,
                    "zero_point": output_zero_point,
                }
            ],
        },
        "memory": {
            "exec_memory_pool": 874512384,
            "exec_memory_size": 1835008,
            "ext_memory_pool": 2415919104,
            "ext_memory_size": 301056,
            "alignment_requirement": 32,
        },
        "postprocess_type": postprocess_type,
        "postprocess_params": {
            "num_classes": num_classes,
            "class_names": class_names,
            "confidence_threshold": confidence_threshold,
            "iou_threshold": iou_threshold,
            "max_detections": max_detections,
            "total_boxes": total_boxes,
            "raw_output_scale": output_scale,
            "raw_output_zero_point": output_zero_point,
        },
        "runtime": {
            "execution": {"mode": "SYNC", "priority": 5, "timeout_ms": 5000},
            "memory_management": {
                "cache_policy": "WRITE_BACK",
                "memory_pool_size": 2097152,
                "garbage_collection": False,
            },
            "debugging": {
                "log_level": "INFO",
                "performance_monitoring": True,
                "memory_profiling": False,
            },
        },
    }
