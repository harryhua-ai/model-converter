"""
NE301 工具链配置管理

支持版本检测和动态适配，兼容 NE301 工具链的后续更新
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime

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
    def parse(version_str: str) -> Optional['NE301Version']:
        """从字符串解析版本号"""
        # 支持格式: "2.0.0.0", "2.0.0", "2.0.0.0-alpha"
        match = re.match(r'(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?(?:-([a-zA-Z0-9]+))?', version_str)
        if match:
            major, minor, patch, build, suffix = match.groups()
            return NE301Version(
                major=int(major),
                minor=int(minor),
                patch=int(patch),
                build=int(build) if build else 0,
                suffix=suffix or ""
            )
        return None

    @staticmethod
    def generate_timestamp_version() -> 'NE301Version':
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
    fw_type_map: Dict[str, int] = field(default_factory=lambda: {
        'fsbl': 0x01,
        'app': 0x02,
        'web': 0x03,
        'ai_model': 0x04,
        'config': 0x05,
        'patch': 0x06,
        'full': 0x07,
    })


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

            if major and minor and patch:
                self.version = NE301Version(
                    major=major,
                    minor=minor,
                    patch=patch,
                    build=build or 0
                )
                logger.info(f"✓ 检测到 NE301 版本: {self.version}")

        except Exception as e:
            logger.warning(f"⚠️  无法解析版本文件: {e}")

    def _extract_version_var(self, content: str, var_name: str, default: int) -> Optional[int]:
        """从 Makefile 内容中提取版本变量"""
        # 匹配: VERSION_MAJOR ?= 2 或 VERSION_MAJOR := 2
        match = re.search(rf'{var_name}\s*:?=\s*(\d+)', content)
        return int(match.group(1)) if match else None

    def _detect_tools(self) -> None:
        """检测可用的打包工具"""
        tools_to_check = {
            'ota_packer': self.project_root / self.config.ota_packer_script,
            'model_packager': self.project_root / self.config.model_packager_script,
            'version_header': self.project_root / self.config.version_header_script,
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
                re.search(r'#\s*Version:\s*([\d.]+)', content),
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
            version = f" ({self.tool_versions.get(tool_name)})" if tool_name in self.tool_versions else ""
            logger.info(f"    {status} {tool_name}{version}")
        logger.info("=" * 50)

    def get_ota_packager(self) -> Optional[Path]:
        """获取 OTA 打包工具路径"""
        tool_name = 'ota_packer'
        if self.available_tools.get(tool_name):
            return self.project_root / self.config.ota_packer_script
        return None

    def get_model_packager(self) -> Optional[Path]:
        """获取模型打包工具路径"""
        tool_name = 'model_packager'
        if self.available_tools.get(tool_name):
            return self.project_root / self.config.model_packager_script
        return None

    def get_model_version(self) -> NE301Version:
        """获取模型版本号"""
        if self.version:
            return self.version
        return NE301Version.generate_timestamp_version()

    def supports_ota_package(self) -> bool:
        """检查是否支持 OTA 打包"""
        return self.available_tools.get('ota_packer', False)

    def supports_model_package(self) -> bool:
        """检查是否支持模型打包"""
        return self.available_tools.get('model_packager', False)

    def get_best_packaging_method(self) -> str:
        """
        获取最佳的打包方式

        Returns:
            'ota': OTA 打包（推荐，兼容设备升级）
            'model': 纯模型打包（备用）
            'fallback': 降级到 TFLite
        """
        if self.supports_ota_package():
            return 'ota'
        elif self.supports_model_package():
            return 'model'
        else:
            return 'fallback'

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

        if packaging_method == 'ota':
            # OTA 固件: ne301_Model_v2.0.0.12345_pkg.bin
            return f"ne301_Model_v{version}_pkg"
        elif packaging_method == 'model':
            # 模型包: ne301_Model_v2.0.0.12345.bin
            return f"ne301_Model_v{version}"
        else:
            # 降级: quantized_model_taskId.tflite
            return f"quantized_model_{task_id}"

    def get_extension(self, packaging_method: str) -> str:
        """获取文件扩展名"""
        if packaging_method in ('ota', 'model'):
            return '.bin'
        else:
            return '.tflite'


class NE301ConfigManager:
    """NE301 配置管理器（单例）"""

    _instance: Optional['NE301ConfigManager'] = None
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


def generate_ne301_json_config(
    tflite_path: Path,
    model_name: str,
    input_size: int,
    num_classes: int,
    class_names: List[str],
    confidence_threshold: float = 0.25,
) -> Dict:
    """
    生成 NE301 模型 JSON 配置

    参考 AIToolStack 的配置格式

    Args:
        tflite_path: TFLite 模型文件路径
        model_name: 模型名称
        input_size: 输入尺寸
        num_classes: 类别数量
        class_names: 类别名称列表
        confidence_threshold: 置信度阈值

    Returns:
        Dict: NE301 JSON 配置
    """
    # 计算输出层的 grid 尺寸（YOLOv8 的特征图）
    # 对于输入尺寸 input_size，特征图通常是 input_size / 8, / 16, / 32
    grid_large = input_size // 8
    grid_medium = input_size // 16
    grid_small = input_size // 32

    # YOLOv8 的输出通道数：num_classes + 4 (box) + 1 (obj)
    output_channels = num_classes + 5

    return {
        "version": "1.0.0",
        "model_info": {
            "name": model_name,
            "version": "1.0.0",
            "description": f"{model_name} - YOLOv8 Object Detection Model",
            "type": "OBJECT_DETECTION",
            "framework": "TFLITE",
            "author": "NE301 Model Converter"
        },
        "input_spec": {
            "width": input_size,
            "height": input_size,
            "channels": 3,
            "data_type": "uint8",
            "color_format": "RGB888_YUV444_1",
            "normalization": {
                "enabled": False,
                "mean": [0.0, 0.0, 0.0],
                "std": [1.0, 1.0, 1.0]
            }
        },
        "output_spec": {
            "num_outputs": 3,
            "outputs": [
                {
                    "name": "output_large",
                    "batch": 1,
                    "height": grid_large,
                    "width": grid_large,
                    "channels": output_channels,
                    "data_type": "float32",
                    "scale": 1.0,
                    "zero_point": 0
                },
                {
                    "name": "output_medium",
                    "batch": 1,
                    "height": grid_medium,
                    "width": grid_medium,
                    "channels": output_channels,
                    "data_type": "float32",
                    "scale": 1.0,
                    "zero_point": 0
                },
                {
                    "name": "output_small",
                    "batch": 1,
                    "height": grid_small,
                    "width": grid_small,
                    "channels": output_channels,
                    "data_type": "float32",
                    "scale": 1.0,
                    "zero_point": 0
                }
            ]
        },
        "memory": {
            "exec_memory_pool": 874512384,
            "exec_memory_size": 1835008,
            "ext_memory_pool": 2415919104,
            "ext_memory_size": 8388608,
            "alignment_requirement": 32
        },
        "postprocess_type": "pp_od_st_yolox_uf",
        "postprocess_params": {
            "num_classes": num_classes,
            "class_names": class_names,
            "confidence_threshold": confidence_threshold,
            "iou_threshold": 0.5,
            "max_detections": 100,
            "scales": {
                "large": {
                    "grid_width": grid_large,
                    "grid_height": grid_large,
                    "anchors": [30.0, 30.0, 4.2, 15.0, 13.8, 42.0]
                },
                "medium": {
                    "grid_width": grid_medium,
                    "grid_height": grid_medium,
                    "anchors": [15.0, 15.0, 2.1, 7.5, 6.9, 21.0]
                },
                "small": {
                    "grid_width": grid_small,
                    "grid_height": grid_small,
                    "anchors": [7.5, 7.5, 1.05, 3.75, 3.45, 10.5]
                }
            }
        },
        "runtime": {
            "execution": {
                "mode": "SYNC",
                "priority": 5,
                "timeout_ms": 5000
            },
            "memory_management": {
                "cache_policy": "WRITE_BACK",
                "memory_pool_size": 2097152,
                "garbage_collection": False
            },
            "debugging": {
                "log_level": "INFO",
                "performance_monitoring": True,
                "memory_profiling": False
            }
        }
    }
