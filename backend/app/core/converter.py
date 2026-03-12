"""
NE301 模型转换核心逻辑

混合方式：
- 步骤 1-2: 宿主机执行（通用 ML 工具链）- 如果可用
- 步骤 3: Docker 容器执行（NE301 专用工具）
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ModelConverter:
    """模型转换器 - PyTorch → NE301 .bin"""

    def __init__(self, work_dir: Optional[Path] = None):
        """
        初始化转换器

        Args:
            work_dir: 工作目录，默认为 temp/converter/
        """
        self.work_dir = work_dir or Path("temp/converter")
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 工具脚本路径
        self.tools_dir = Path(__file__).parent.parent.parent / "tools"
        self.quant_script = self.tools_dir / "tflite_quant.py"
        self.quant_config_template = self.tools_dir / "user_config_quant.yaml"

        # 检测依赖可用性
        self._ultralytics_available = self._check_import("ultralytics")
        self._tensorflow_available = self._check_import("tensorflow")

        if not self._ultralytics_available or not self._tensorflow_available:
            logger.warning(
                "ML 库不可用。步骤 1-2 将需要在 Docker 容器中执行。"
                "请安装: pip install ultralytics tensorflow"
            )

    def _check_import(self, module_name: str) -> bool:
        """检查模块是否可导入"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def convert(
        self,
        model_path: str,
        config: Dict[str, Any],
        calib_dataset_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        完整转换流程：PyTorch → TFLite → 量化 → NE301 .bin

        Args:
            model_path: PyTorch 模型路径 (.pt/.pth)
            config: 转换配置
            calib_dataset_path: 校准数据集路径（可选）
            progress_callback: 进度回调函数

        Returns:
            NE301 .bin 文件路径

        Raises:
            RuntimeError: 如果 ML 库不可用
        """
        task_id = config.get("task_id", "unknown")

        # 检查依赖
        if not self._ultralytics_available or not self._tensorflow_available:
            raise RuntimeError(
                "ML 库不可用。请安装: pip install ultralytics tensorflow\n"
                "或者使用 Python 3.11/3.12 环境"
            )

        # 步骤 1: PyTorch → TFLite (0-30%)
        if progress_callback:
            progress_callback(10, "正在导出 TFLite 模型...")

        tflite_path = self._pytorch_to_tflite(
            model_path,
            config["input_size"]
        )

        # 步骤 2: TFLite → 量化 TFLite (30-70%)
        if progress_callback:
            progress_callback(30, "正在量化模型...")

        quantized_tflite = self._quantize_tflite(
            tflite_path,
            config["input_size"],
            calib_dataset_path
        )

        # 步骤 3: 量化 TFLite → NE301 .bin (70-100%)
        if progress_callback:
            progress_callback(70, "正在生成 NE301 部署包...")

        from app.core.docker_adapter import DockerToolChainAdapter

        docker = DockerToolChainAdapter()
        bin_path = docker.convert_model(
            task_id=task_id,
            model_path=str(quantized_tflite),
            config=config
        )

        if progress_callback:
            progress_callback(100, "转换完成!")

        return bin_path

    def _pytorch_to_tflite(
        self,
        model_path: str,
        input_size: int
    ) -> Path:
        """
        步骤 1: PyTorch → TFLite

        Args:
            model_path: PyTorch 模型路径
            input_size: 输入尺寸

        Returns:
            TFLite 文件路径

        Raises:
            FileNotFoundError: 如果 TFLite 导出失败
        """
        from ultralytics import YOLO

        logger.info(f"步骤 1: 导出 {model_path} 为 TFLite 格式")

        # 使用 Ultralytics 导出
        model = YOLO(model_path)

        # 执行导出
        model.export(
            format="tflite",
            imgsz=input_size,
            int8=False  # 先不量化，后面用 ST 脚本量化
        )

        # Ultralytics 会生成与模型同名的 .tflite 文件
        tflite_path = Path(model_path).stem + ".tflite"

        if not Path(tflite_path).exists():
            raise FileNotFoundError(f"TFLite 导出失败: {tflite_path}")

        logger.info(f"✅ TFLite 导出成功: {tflite_path}")
        return Path(tflite_path)

    def _quantize_tflite(
        self,
        tflite_path: Path,
        input_size: int,
        calib_dataset_path: Optional[str] = None
    ) -> Path:
        """
        步骤 2: TFLite → 量化 TFLite

        使用 ST Microelectronics 的量化脚本

        Args:
            tflite_path: TFLite 模型路径
            input_size: 输入尺寸
            calib_dataset_path: 校准数据集路径

        Returns:
            量化后的 TFLite 文件路径

        Raises:
            RuntimeError: 如果量化失败
            FileNotFoundError: 如果量化后的模型未找到
        """
        logger.info(f"步骤 2: 量化 {tflite_path}")

        # 首先将 TFLite 转换为 SavedModel 格式（tflite_quant.py 需要）
        saved_model_path = self._convert_tflite_to_saved_model(tflite_path)

        # 准备配置文件
        config_path = self._prepare_quant_config(
            saved_model_path,
            input_size,
            calib_dataset_path
        )

        # 执行量化脚本
        cmd = [
            "python",
            str(self.quant_script),
            "--config-name", "user_config_quant",
            "--config-dir", str(self.tools_dir)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )

        if result.returncode != 0:
            logger.error(f"量化失败: {result.stderr}")
            raise RuntimeError(f"TFLite 量化失败: {result.stderr}")

        # 查找生成的量化模型
        quantized_dir = self.work_dir / "quantized_models"
        quantized_models = list(quantized_dir.glob("*.tflite"))

        if not quantized_models:
            raise FileNotFoundError("量化后的模型文件未找到")

        logger.info(f"✅ 量化成功: {quantized_models[0]}")
        return quantized_models[0]

    def _convert_tflite_to_saved_model(self, tflite_path: Path) -> Path:
        """
        将 TFLite 模型转换为 SavedModel 格式

        Args:
            tflite_path: TFLite 模型路径

        Returns:
            SavedModel 目录路径
        """
        import tensorflow as tf

        # 加载 TFLite 模型
        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()

        # 获取输入输出详情
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        # 创建 SavedModel
        saved_model_path = self.work_dir / "saved_model"

        # 定义签名
        @tf.function(input_signature=[
            tf.TensorSpec(
                shape=input_details[0]['shape'],
                dtype=tf.float32,
                name=input_details[0]['name']
            )
        ])
        def model_fn(inputs):
            interpreter.set_tensor(input_details[0]['index'], inputs)
            interpreter.invoke()
            output = interpreter.get_tensor(output_details[0]['index'])
            return {output_details[0]['name']: output}

        # 保存为 SavedModel 格式
        tf.saved_model.save(
            model_fn,
            str(saved_model_path),
            signatures=tf.saved_model.serve(model_fn)
        )

        return saved_model_path

    def _prepare_quant_config(
        self,
        saved_model_path: Path,
        input_size: int,
        calib_dataset_path: Optional[str]
    ) -> Path:
        """
        准备量化配置文件

        Args:
            saved_model_path: SavedModel 路径
            input_size: 输入尺寸
            calib_dataset_path: 校准数据集路径

        Returns:
            配置文件路径
        """
        import yaml

        # 读取模板
        with open(self.quant_config_template) as f:
            config = yaml.safe_load(f)

        # 更新配置
        config["model"]["model_path"] = str(saved_model_path)
        config["model"]["input_shape"] = [input_size, input_size, 3]

        if calib_dataset_path:
            config["quantization"]["calib_dataset_path"] = calib_dataset_path
        else:
            # 使用默认的少量图片
            config["quantization"]["calib_dataset_path"] = str(
                self.work_dir / "default_calib"
            )

        # 保存到工作目录
        config_path = self.work_dir / "user_config_quant.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path
