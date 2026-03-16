"""
Docker 工具链适配器（容器化版本 + 性能优化）

参考：camthink-ai/AIToolStack/backend/utils/ne301_export.py

性能优化：
- 集成性能监控
- 缓存 Docker 路径映射
- 复用 Docker 客户端
- 实时日志推送
"""
import docker
import subprocess
import logging
import threading
import time
import json
import os
import shutil
import yaml
import numpy as np
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List, Tuple
from functools import lru_cache
import tempfile
import zipfile

from .config import settings
from .ne301_config import get_ne301_toolchain, generate_ne301_json_config
from .performance_monitor import get_performance_monitor, PerformanceMonitor
from .task_manager import get_task_manager

logger = logging.getLogger(__name__)


class DockerToolChainAdapter:
    """Docker 工具链适配器（优化版）"""

    # 类级别的 Docker 客户端（复用）
    _docker_client: Optional[docker.DockerClient] = None
    _client_lock = threading.Lock()

    # 路径映射缓存
    _path_cache: Dict[str, str] = {}
    _path_cache_lock = threading.Lock()

    def __init__(self):
        self.ne301_image = settings.NE301_DOCKER_IMAGE
        self.ne301_project_path = Path(settings.NE301_PROJECT_PATH)

        # 使用类级别的共享客户端
        if DockerToolChainAdapter._docker_client is None:
            with DockerToolChainAdapter._client_lock:
                if DockerToolChainAdapter._docker_client is None:
                    try:
                        DockerToolChainAdapter._docker_client = docker.from_env()
                        logger.info(f"Docker 客户端初始化成功，NE301 镜像: {self.ne301_image}")
                    except Exception as e:
                        logger.error(f"Failed to initialize Docker client: {e}")

        self.client = DockerToolChainAdapter._docker_client

        # 获取性能监控器
        self.performance_monitor = get_performance_monitor()

    def check_docker(self) -> tuple[bool, str]:
        """检查 Docker 是否可用

        Returns:
            (是否可用, 错误信息)
        """
        if not self.client:
            return False, "Docker client not available"

        try:
            self.client.ping()
            return True, ""
        except docker.errors.DockerException as e:
            return False, f"Docker not available: {str(e)}"

    def check_image(self) -> bool:
        """检查 NE301 镜像是否存在

        Returns:
            镜像是否存在
        """
        if not self.client:
            return False

        try:
            self.client.images.get(self.ne301_image)
            return True
        except docker.errors.ImageNotFound:
            return False
        except Exception as e:
            logger.error(f"检查镜像失败: {e}")
            return False

    # ============================================================
    # NE301 模型转换量化流程核心函数
    # ============================================================

    def _export_to_saved_model(
        self,
        model_path: str,
        input_size: int
    ) -> str:
        """导出 SavedModel 格式（使用 Ultralytics）

        Args:
            model_path: PyTorch 模型路径
            input_size: 输入尺寸

        Returns:
            SavedModel 目录路径

        Raises:
            FileNotFoundError: 模型文件不存在
            RuntimeError: 导出失败
        """
        from ultralytics import YOLO

        logger.info(f"导出 SavedModel 格式")
        logger.info(f"  模型: {model_path}")
        logger.info(f"  输入尺寸: {input_size}x{input_size}")

        # 验证模型文件存在
        if not Path(model_path).exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        try:
            # 加载 YOLO 模型
            model = YOLO(model_path)

            # 创建临时输出目录
            temp_dir = tempfile.mkdtemp(prefix="saved_model_")
            export_path = Path(temp_dir) / "saved_model"

            # 导出为 SavedModel 格式
            model.export(
                format="saved_model",
                imgsz=input_size,
                half=False  # 使用 float32（后续量化时会转换）
            )

            # 确保返回的是 SavedModel 目录
            if not export_path.exists():
                # Ultralytics 可能返回了不同的路径
                saved_model_paths = list(Path(temp_dir).glob("saved_model"))
                if saved_model_paths:
                    export_path = saved_model_paths[0]
                else:
                    raise RuntimeError(f"SavedModel 目录未生成: {export_path}")

            logger.info(f"✅ SavedModel 导出成功: {export_path}")
            return str(export_path)

        except Exception as e:
            logger.error(f"❌ SavedModel 导出失败: {e}")
            raise RuntimeError(f"SavedModel 导出失败: {e}") from e

    def _prepare_quant_config(
        self,
        saved_model_path: str,
        input_size: int,
        calib_dataset_path: Optional[str] = None
    ) -> Path:
        """准备 ST 量化配置文件 (YAML)

        Args:
            saved_model_path: SavedModel 目录路径
            input_size: 输入尺寸
            calib_dataset_path: 校准数据集路径（可选）

        Returns:
            配置文件路径
        """
        logger.info(f"准备量化配置文件")

        # 处理校准数据集路径
        actual_calib_path = calib_dataset_path
        if calib_dataset_path and calib_dataset_path.endswith('.zip'):
            actual_calib_path = self._extract_calibration_dataset(calib_dataset_path)

        # 创建配置文件
        config_data = {
            "model": {
                "name": "yolov8n_custom",
                "uc": "od_coco",
                "model_path": saved_model_path,
                "input_shape": [input_size, input_size, 3]
            },
            "quantization": {
                "fake": actual_calib_path is None,  # 如果无校准数据集，使用 fake 量化
                "quantization_type": "per_channel",
                "quantization_input_type": "uint8",
                "quantization_output_type": "int8",
                "calib_dataset_path": actual_calib_path or "",
                "export_path": "./quantized_models",
                "max_calib_images": 200  # 限制校准图片数量防止 OOM
            },
            "pre_processing": {
                "rescaling": {"scale": 255, "offset": 0}
            }
        }

        # 写入临时 YAML 文件
        temp_dir = tempfile.mkdtemp(prefix="quant_config_")
        config_path = Path(temp_dir) / "user_config_quant.yaml"

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"✅ 配置文件已生成: {config_path}")
        if actual_calib_path:
            logger.info(f"  使用校准数据集: {actual_calib_path}")
        else:
            logger.info(f"  使用 fake 量化模式")

        return config_path

    def _run_st_quantization(
        self,
        saved_model_path: str,
        input_size: int,
        calib_dataset_path: Optional[str],
        output_dir: str
    ) -> str:
        """运行 ST 官方量化脚本

        Args:
            saved_model_path: SavedModel 路径
            input_size: 输入尺寸
            calib_dataset_path: 校准数据集路径
            output_dir: 输出目录

        Returns:
            量化后的 TFLite 文件路径

        Raises:
            RuntimeError: 量化失败
        """
        logger.info(f"运行 ST 官方量化脚本")

        # 步骤 1: 准备量化配置
        config_path = self._prepare_quant_config(
            saved_model_path=saved_model_path,
            input_size=input_size,
            calib_dataset_path=calib_dataset_path
        )

        # 步骤 2: 获取量化脚本路径
        quant_script = Path(__file__).parent.parent.parent / "tools" / "quantization" / "tflite_quant.py"

        if not quant_script.exists():
            raise RuntimeError(f"量化脚本不存在: {quant_script}")

        # 步骤 3: 构造命令（使用 subprocess 安全调用）
        cmd = [
            "python3",
            str(quant_script),
            "--config-path", str(config_path.parent),  # Hydra 配置目录
            "--config-name", "user_config_quant"        # 配置文件名（不含 .yaml）
        ]

        logger.info(f"执行命令: {' '.join(cmd)}")

        try:
            # 步骤 4: 执行量化脚本
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 分钟超时
                cwd=str(config_path.parent)
            )

            if result.returncode != 0:
                error_output = result.stderr[-500:] if result.stderr else result.stdout[-500:]
                logger.error(f"❌ 量化脚本执行失败:")
                logger.error(f"  退出码: {result.returncode}")
                logger.error(f"  错误输出:\n{error_output}")
                raise RuntimeError(f"量化失败: {error_output}")

            # 步骤 5: 查找生成的量化文件
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # 从配置目录复制量化文件到输出目录
            source_dir = Path(config_path.parent) / "quantized_models"
            if not source_dir.exists():
                raise FileNotFoundError(f"量化输出目录不存在: {source_dir}")

            # 查找 .tflite 文件
            tflite_files = list(source_dir.glob("*.tflite"))
            if not tflite_files:
                raise FileNotFoundError(f"量化文件未生成（目录: {source_dir}）")

            # 返回最新的文件
            quantized_file = max(tflite_files, key=lambda p: p.stat().st_mtime)
            
            # 复制到输出目录
            output_file = output_path / quantized_file.name
            shutil.copy2(quantized_file, output_file)
            
            logger.info(f"✅ 量化完成: {output_file}")
            return str(output_file)

        except subprocess.TimeoutExpired:
            logger.error(f"❌ 量化超时（>10分钟）")
            raise RuntimeError("量化超时")
        except Exception as e:
            logger.error(f"❌ 量化失败: {e}")
            raise RuntimeError(f"量化失败: {e}") from e

    def _validate_quantized_model(
        self,
        tflite_path: str,
        input_size: int
    ) -> bool:
        """验证量化后的模型

        检查：
        - 输出形状正确（根据输入尺寸）
        - 量化参数有效（scale != 1.0）

        Args:
            tflite_path: 量化 TFLite 路径
            input_size: 输入尺寸

        Returns:
            验证是否通过

        Raises:
            FileNotFoundError: 模型文件不存在
            RuntimeError: 无效的 TFLite 模型
            ValueError: 输出形状错误
        """
        import tensorflow as tf

        logger.info(f"验证量化模型")

        # 验证文件存在
        if not Path(tflite_path).exists():
            raise FileNotFoundError(f"量化模型文件不存在: {tflite_path}")

        try:
            # 加载 TFLite 模型
            interpreter = tf.lite.Interpreter(model_path=tflite_path)
            interpreter.allocate_tensors()

            # 获取输入输出详情
            input_details = interpreter.get_input_details()[0]
            output_details = interpreter.get_output_details()[0]

            logger.info(f"  输入形状: {input_details['shape']}")
            logger.info(f"  输出形状: {output_details['shape']}")

            # 验证输出形状
            expected_boxes = {
                256: 1344,
                320: 2100,
                416: 3549,
                512: 5376,
                640: 8400,
            }

            output_shape = output_details['shape']
            if input_size in expected_boxes:
                expected = expected_boxes[input_size]
                actual_boxes = output_shape[2] if len(output_shape) > 2 else output_shape[1]

                if actual_boxes != expected:
                    error_msg = (
                        f"输出形状错误: 预期 (1, 34, {expected})，"
                        f"实际 {output_shape}"
                    )
                    logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg)

                logger.info(f"✅ 输出形状正确 (total_boxes={actual_boxes})")
            else:
                logger.warning(f"⚠️  未知输入尺寸 {input_size}，跳过形状验证")

            # 验证量化参数
            if 'quantization_parameters' in output_details:
                quant_params = output_details['quantization_parameters']
                scales = quant_params.get('scales', [])

                if scales and len(scales) > 0:
                    scale = float(scales[0])
                    logger.info(f"  量化 scale: {scale}")

                    # 检查 scale 是否合理（不应该是 1.0，除非是 float32）
                    if scale == 1.0 and output_details.get('dtype') != np.float32:
                        logger.warning(f"⚠️  量化 scale 为 1.0，可能未正确量化")
                else:
                    logger.warning(f"⚠️  未找到量化参数")
            else:
                logger.warning(f"⚠️  模型输出没有量化参数")

            logger.info(f"✅ 模型验证通过")
            return True

        except Exception as e:
            logger.error(f"❌ 模型验证失败: {e}")
            if "TFLite" in str(e) or "interpreter" in str(e):
                raise RuntimeError(f"无效的 TFLite 模型: {e}") from e
            raise

    def _extract_calibration_dataset(self, calib_dataset_path: str) -> str:
        """
        解压校准数据集 ZIP 文件并返回图片目录路径

        Args:
            calib_dataset_path: 校准数据集 ZIP 文件路径

        Returns:
            解压后的图片目录路径

        Raises:
            RuntimeError: 如果解压失败或找不到图片
        """
        if not calib_dataset_path or not calib_dataset_path.endswith('.zip'):
            return calib_dataset_path

        logger.info(f"检测到校准数据集是 ZIP 文件，正在解压...")

        extract_dir = tempfile.mkdtemp(prefix="calibration_")

        try:
            with zipfile.ZipFile(calib_dataset_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            logger.info(f"✅ 校准数据集已解压到: {extract_dir}")

            # 查找解压后的目录
            for root, dirs, files in os.walk(extract_dir):
                image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if image_files:
                    logger.info(f"✅ 找到校准图片目录: {root} (包含 {len(image_files)} 张图片)")
                    return root

            logger.warning(f"解压后未找到有效的校准图片，将使用解压目录")
            return extract_dir

        except Exception as e:
            logger.error(f"解压校准数据集失败: {e}")
            raise RuntimeError(f"解压校准数据集失败: {e}")
