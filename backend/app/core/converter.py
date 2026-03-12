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

        from .docker_adapter import DockerToolChainAdapter

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

        # Ultralytics 会生成 {stem}_float32.tflite 文件
        # 文件可能生成在模型所在目录或当前工作目录
        model_dir = Path(model_path).parent
        model_stem = Path(model_path).stem

        # 尝试多个可能的路径
        # 注意：YOLOv8 可能将 TFLite 文件放在 SavedModel 子目录中
        saved_model_dir = model_dir / f"{model_stem}_saved_model"
        possible_paths = [
            saved_model_dir / f"{model_stem}_float32.tflite",  # SavedModel 子目录（新版本 YOLO）
            saved_model_dir / f"{model_stem}.tflite",           # SavedModel 子目录（旧命名）
            model_dir / f"{model_stem}_float32.tflite",         # 模型所在目录
            Path(f"{model_stem}_float32.tflite"),               # 当前工作目录
            model_dir / f"{model_stem}.tflite",                 # 旧命名方式（模型目录）
            Path(f"{model_stem}.tflite")                        # 旧命名方式（当前目录）
        ]

        tflite_path = None
        for path in possible_paths:
            if path.exists():
                tflite_path = path
                break

        if tflite_path is None:
            raise FileNotFoundError(f"TFLite 导出失败: 未找到生成的文件。已尝试: {possible_paths}")

        logger.info(f"✅ TFLite 导出成功: {tflite_path}")
        return tflite_path

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

        # 获取对应的 SavedModel 目录（Ultralytics 导出时已生成）
        saved_model_path = self._get_saved_model_path(tflite_path)

        # 准备校准数据集路径
        if calib_dataset_path:
            calib_path = str(Path(calib_dataset_path).resolve())
        else:
            # 创建默认校准数据集目录（空目录，使用 fake quantization）
            default_calib = self.work_dir / "default_calib"
            default_calib.mkdir(exist_ok=True)
            calib_path = str(default_calib.resolve())

        # 准备输出目录（使用绝对路径）
        export_path = str((self.work_dir / "quantized_models").resolve())

        logger.info(f"SavedModel 路径: {saved_model_path}")
        logger.info(f"校准数据集: {calib_path}")
        logger.info(f"输出目录: {export_path}")

        # 执行量化脚本，使用 Hydra override 语法传递绝对路径
        # 这样可以绕过配置文件加载问题，直接设置参数
        # 注意：使用 sys.executable 确保使用当前 Python 环境
        import sys

        cmd = [
            sys.executable,  # 使用当前 Python 解释器
            str(self.quant_script),
            f"model.model_path={saved_model_path.resolve()}",
            f"model.input_shape=[{input_size},{input_size},3]",
            f"quantization.calib_dataset_path={calib_path}",
            f"quantization.export_path={export_path}"
        ]

        logger.info(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )

        if result.returncode != 0:
            logger.error(f"量化命令: {' '.join(cmd)}")
            logger.error(f"量化失败: {result.stderr}")
            logger.error(f"标准输出: {result.stdout}")
            raise RuntimeError(f"TFLite 量化失败: {result.stderr}")

        # 查找生成的量化模型
        quantized_dir = self.work_dir / "quantized_models"
        quantized_models = list(quantized_dir.glob("*.tflite"))

        if not quantized_models:
            raise FileNotFoundError("量化后的模型文件未找到")

        logger.info(f"✅ 量化成功: {quantized_models[0]}")
        return quantized_models[0]

    def _get_saved_model_path(
        self,
        tflite_path: Path
    ) -> Path:
        """
        获取对应的 SavedModel 目录路径

        注意：Ultralytics 导出 TFLite 时会同时生成 SavedModel 格式
        我们直接使用那个 SavedModel，而不是从 TFLite 转换

        Args:
            tflite_path: TFLite 模型路径

        Returns:
            SavedModel 目录路径

        Raises:
            FileNotFoundError: 如果 SavedModel 目录不存在
        """
        # TFLite 文件在 SavedModel 子目录中
        # 例如: best_saved_model/best_float32.tflite
        # SavedModel 目录就是: best_saved_model/
        if tflite_path.parent.name.endswith("_saved_model"):
            saved_model_path = tflite_path.parent
        else:
            # 如果 TFLite 不在 SavedModel 子目录中，
            # 尝试找到对应的 SavedModel 目录
            model_stem = tflite_path.stem.replace("_float32", "").replace("_int8", "")
            saved_model_path = tflite_path.parent / f"{model_stem}_saved_model"

        if not saved_model_path.exists():
            raise FileNotFoundError(
                f"SavedModel 目录不存在: {saved_model_path}\n"
                f"请确保 Ultralytics 导出时生成了 SavedModel 格式"
            )

        # 验证这是有效的 SavedModel
        if not (saved_model_path / "saved_model.pb").exists():
            raise FileNotFoundError(
                f"目录不是有效的 SavedModel: {saved_model_path}\n"
                f"缺少 saved_model.pb 文件"
            )

        logger.info(f"✅ 找到 SavedModel: {saved_model_path}")
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
        # 使用绝对路径避免 Hydra 执行目录问题
        config["model"]["model_path"] = str(saved_model_path.resolve())
        config["model"]["input_shape"] = [input_size, input_size, 3]

        if calib_dataset_path:
            config["quantization"]["calib_dataset_path"] = str(Path(calib_dataset_path).resolve())
        else:
            # 使用默认的少量图片
            config["quantization"]["calib_dataset_path"] = str(
                (self.work_dir / "default_calib").resolve()
            )

        # 导出路径也使用绝对路径
        config["quantization"]["export_path"] = str((self.work_dir / "quantized_models").resolve())

        # 保存到工作目录
        config_path = self.work_dir / "user_config_quant.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        return config_path
