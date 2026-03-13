"""
模型转换服务
实现 PyTorch → TFLite → network_rel.bin → ZIP 的完整转换流程
"""
import os
import subprocess
import json
import yaml
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

# 可选导入 ML 库（用于实际转换）
try:
    from ultralytics import YOLO
    ML_AVAILABLE = True
except ImportError:
    YOLO = None
    ML_AVAILABLE = False

import structlog

from app.models.schemas import ConversionConfig, ConversionProgress, TaskStatus
from app.core.config import settings

logger = structlog.get_logger(__name__)


def _get_stedgeai_env() -> dict:
    """
    获取包含 stedgeai PATH 的环境变量字典
    stedgeai 在 ne301-dev 镜像里位于 /opt/stedgeai/VERSION/Utilities/linux/
    """
    env = os.environ.copy()

    stedgeai_root = os.environ.get("STEDGEAI_PATH", "/opt/stedgeai")

    # 查找实际的 stedgeai 可执行文件目录
    if os.path.exists(stedgeai_root):
        for item in sorted(os.listdir(stedgeai_root)):
            candidate = os.path.join(stedgeai_root, item, "Utilities", "linux")
            if os.path.isdir(candidate):
                env["PATH"] = candidate + ":" + env.get("PATH", "")
                env["STEDGEAI_CORE_DIR"] = os.path.join(stedgeai_root, item)
                logger.info("发现 stedgeai", path=candidate)
                break

    # 同时加载 /etc/profile.d/stedgeai.sh 中定义的路径
    profile_script = "/etc/profile.d/stedgeai.sh"
    if os.path.exists(profile_script):
        with open(profile_script) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export PATH"):
                    extra_path = line.split("=", 1)[-1].strip().strip('"').replace("$PATH:", "")
                    env["PATH"] = extra_path + ":" + env.get("PATH", "")
                elif line.startswith("export STEDGEAI_CORE_DIR"):
                    env["STEDGEAI_CORE_DIR"] = line.split("=", 1)[-1].strip().strip('"')

    return env


class ConversionService:
    """模型转换服务"""

    def __init__(self):
        """初始化转换服务"""
        self.ne301_path = settings.NE301_PROJECT_PATH
        self.script_path = os.path.join(self.ne301_path, "Script")
        self.generate_script = os.path.join(self.script_path, "generate-reloc-model.sh")
        self.packager_script = os.path.join(self.script_path, "model_packager.py")

    async def _check_cancelled(self, task_id: str) -> bool:
        """
        检查任务是否已被取消

        Args:
            task_id: 任务 ID

        Returns:
            bool: 如果任务已取消返回 True

        Raises:
            RuntimeError: 如果任务已取消
        """
        from app.services.task_manager import get_task_manager

        task_manager = get_task_manager()
        task = await task_manager.get_task(task_id)

        if task and task.status == TaskStatus.CANCELLED:
            logger.info("检测到任务取消请求，终止转换", task_id=task_id)
            raise RuntimeError("任务已被用户取消")

        return False

    async def convert_model(
        self,
        task_id: str,
        input_path: str,
        calibration_dataset_path: str | None = None,
        class_yaml_path: str | None = None,
        config: ConversionConfig | None = None,
    ) -> None:
        """
        执行完整的模型转换流程

        Args:
            task_id: 任务 ID
            input_path: 输入模型路径
            calibration_dataset_path: 校准数据集 zip 文件路径 (可选)
            class_yaml_path: data.yaml 类别配置文件路径 (可选)
            config: 转换配置

        转换流程:
            1. Extracting calibration dataset
            2. PyTorch → TFLite (INT8 量化)
            3. TFLite → network_rel.bin (stedgeai)
            4. 生成模型配置 JSON
            5. 打包成 ZIP 文件
        """
        try:
            if not ML_AVAILABLE:
                raise ImportError(
                    "ML libraries not installed (ultralytics/torch). Please confirm Docker environment is properly built."
                )

            # 检查取消状态
            await self._check_cancelled(task_id)

            await self._update_progress(
                task_id,
                status=TaskStatus.VALIDATING,
                progress=5,
                current_step="Validating model file",
            )

            # 创建临时工作目录
            work_dir = os.path.join(settings.TEMP_DIR, task_id)
            os.makedirs(work_dir, exist_ok=True)

            logger.info(
                "开始模型转换",
                task_id=task_id,
                config=config.model_dump() if config else None,
                has_calibration=calibration_dataset_path is not None,
                has_class_yaml=class_yaml_path is not None,
            )

            # 检查取消状态
            await self._check_cancelled(task_id)

            # 处理校准数据集
            calib_dataset_path = None
            if calibration_dataset_path and config and config.use_custom_calibration:
                await self._update_progress(
                    task_id, progress=7, current_step="Extracting calibration dataset"
                )
                calib_dataset_path = await self._extract_calibration_dataset(
                    zip_path=calibration_dataset_path,
                    work_dir=work_dir,
                )

            # 检查取消状态
            await self._check_cancelled(task_id)

            # 准备 data.yaml (用于 INT8 量化校准)
            effective_data_yaml = None
            if class_yaml_path and os.path.exists(class_yaml_path):
                # 使用用户上传的 data.yaml，但更新图像路径指向解压后的校准数据集
                effective_data_yaml = await self._prepare_data_yaml(
                    user_yaml_path=class_yaml_path,
                    calib_path=calib_dataset_path,
                    work_dir=work_dir,
                )

            # 检查取消状态
            await self._check_cancelled(task_id)

            # Step 1: PyTorch → TFLite
            await self._update_progress(
                task_id,
                status=TaskStatus.CONVERTING,
                progress=10,
                current_step="Converting to TFLite...",
            )

            tflite_path = await self._convert_to_tflite(
                input_path=input_path,
                work_dir=work_dir,
                config=config,
                task_id=task_id,
                calib_dataset_path=calib_dataset_path,
                data_yaml_path=effective_data_yaml,
            )

            # 检查取消状态
            await self._check_cancelled(task_id)

            # 定位 INT8 TFLite 文件（Ultralytics 会生成多个版本）
            tflite_int8_path = self._find_int8_tflite(tflite_path, task_id)
            if tflite_int8_path:
                logger.info("找到 INT8 TFLite 文件", path=tflite_int8_path)
                tflite_path = tflite_int8_path
            else:
                logger.warning("未找到 INT8 TFLite 文件，使用默认路径", path=tflite_path)

            # 检查取消状态
            await self._check_cancelled(task_id)

            # Step 2: TFLite → network_rel.bin
            await self._update_progress(
                task_id, progress=40, current_step="Generating C model..."
            )

            network_bin_path = await self._generate_network_bin(
                tflite_path=tflite_path,
                work_dir=work_dir,
                config=config,
                task_id=task_id,
            )

            # 检查取消状态
            await self._check_cancelled(task_id)

            # Step 3: 生成模型配置 JSON
            await self._update_progress(
                task_id, progress=70, current_step="Generating configuration..."
            )

            config_json_path = await self._generate_config_json(
                work_dir=work_dir,
                config=config,
                tflite_path=tflite_path,
            )

            # 检查取消状态
            await self._check_cancelled(task_id)

            # Step 4: 打包 ZIP
            await self._update_progress(
                task_id,
                status=TaskStatus.PACKAGING,
                progress=85,
                current_step="Packaging ZIP...",
            )

            output_filename = await self._package_model(
                network_bin=network_bin_path,
                config_json=config_json_path,
                config=config,
                work_dir=work_dir,
            )

            # 完成
            await self._update_progress(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                current_step="Conversion completed ✓",
                output_filename=output_filename,
            )

            logger.info("模型转换完成", task_id=task_id, output_filename=output_filename)

        except RuntimeError as e:
            # 检查是否是取消异常
            if "任务已被用户取消" in str(e):
                logger.info("任务已取消，清理临时文件", task_id=task_id)
                # 清理临时文件
                self._cleanup_task_files(task_id)
                # 状态已由 cancel_task 更新，无需再次更新
            else:
                raise
        except Exception as e:
            logger.error("模型转换失败", task_id=task_id, error=str(e))
            await self._update_progress(
                task_id,
                status=TaskStatus.FAILED,
                current_step=f"Conversion failed: {str(e)}",
                error=str(e),
            )

    def _cleanup_task_files(self, task_id: str) -> None:
        """清理任务相关的临时文件"""
        try:
            import shutil
            from app.core.config import settings

            work_dir = os.path.join(settings.TEMP_DIR, task_id)
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir)
                logger.info("已清理临时目录", task_id=task_id, path=work_dir)
        except Exception as e:
            logger.warning("清理临时文件失败", task_id=task_id, error=str(e))

    async def _extract_calibration_dataset(self, zip_path: str, work_dir: str) -> str:
        """Extracting calibration dataset ZIP 文件"""
        try:
            extract_dir = os.path.join(work_dir, "calibration_dataset")
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            logger.info("Calibration dataset extracted successfully", extract_dir=extract_dir)

            # 查找图像目录
            images_dir = self._find_images_dir(extract_dir)
            image_files = [
                f for f in os.listdir(images_dir)
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
            ]

            if len(image_files) == 0:
                raise RuntimeError("校准数据集中未找到图像文件")

            logger.info("校准数据集验证通过", image_count=len(image_files))
            return extract_dir

        except zipfile.BadZipFile:
            raise RuntimeError("校准数据集 ZIP 文件损坏")
        except Exception as e:
            raise RuntimeError(f"Extracting calibration dataset失败: {str(e)}")

    def _find_images_dir(self, base_dir: str) -> str:
        """在目录中查找包含图像的子目录"""
        candidates = [
            os.path.join(base_dir, "images"),
            os.path.join(base_dir, "calibration"),  # 优先级提高！
            os.path.join(base_dir, "val"),
            os.path.join(base_dir, "train"),
            base_dir,
        ]
        for d in candidates:
            if os.path.isdir(d):
                files = [f for f in os.listdir(d)
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                if files:
                    return d
        return base_dir

    def _find_int8_tflite(self, tflite_path: str, task_id: str) -> str | None:
        """
        在 Ultralytics 导出目录中查找 INT8 量化的 TFLite 文件

        Ultralytics TFLite 导出会生成多个文件：
        - best_float32.tflite
        - best_float16.tflite
        - best_integer_quant.tflite  ← INT8 量化版本（我们需要的）
        - best_dynamic_range_quant.tflite

        Args:
            tflite_path: Ultralytics 导出的路径（可能是 saved_model 目录或具体文件）
            task_id: 任务 ID，用于文件名匹配

        Returns:
            INT8 TFLite 文件的完整路径，如果找不到则返回 None
        """
        try:
            # 如果 tflite_path 是具体文件，直接检查
            if os.path.isfile(tflite_path):
                if "int8" in tflite_path.lower() or "integer" in tflite_path.lower():
                    return tflite_path
                return None

            # 如果是目录，查找 INT8 文件
            if os.path.isdir(tflite_path):
                # 优先查找 best_integer_quant.tflite
                candidates = [
                    "best_integer_quant.tflite",
                    "best_int8.tflite",
                    f"{task_id}_best_integer_quant.tflite",
                    f"{task_id}_best_int8.tflite",
                ]

                for filename in candidates:
                    full_path = os.path.join(tflite_path, filename)
                    if os.path.exists(full_path):
                        return full_path

                # 如果以上都找不到，列出目录中所有的 .tflite 文件
                for root, dirs, files in os.walk(tflite_path):
                    for file in files:
                        if file.endswith(".tflite"):
                            file_lower = file.lower()
                            if "int8" in file_lower or "integer" in file_lower:
                                return os.path.join(root, file)

            return None
        except Exception as e:
            logger.warning("查找 INT8 TFLite 文件失败", error=str(e))
            return None

    async def _prepare_data_yaml(
        self,
        user_yaml_path: str,
        calib_path: str | None,
        work_dir: str,
    ) -> str:
        """
        准备 Ultralytics data.yaml:
        - 使用用户提供的 data.yaml 中的 nc 和 names
        - 将图像路径改为解压后的校准数据集路径
        """
        try:
            with open(user_yaml_path, 'r', encoding='utf-8') as f:
                user_data = yaml.safe_load(f)

            # 使用校准数据集路径（如果有），否则保留原始路径
            if calib_path:
                images_dir = self._find_images_dir(calib_path)
                user_data['path'] = calib_path
                user_data['train'] = os.path.relpath(images_dir, calib_path)
                user_data['val'] = os.path.relpath(images_dir, calib_path)
            else:
                # 如果没有校准数据集，保留原始路径（可能无效，但不会崩溃）
                pass

            output_path = os.path.join(work_dir, "data.yaml")
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(user_data, f, allow_unicode=True)

            logger.info("data.yaml 准备完成", path=output_path, nc=user_data.get('nc'))
            return output_path

        except Exception as e:
            logger.warning("Failed to prepare data.yaml, will auto-generate", error=str(e))
            return None

    async def _convert_to_tflite(
        self,
        input_path: str,
        work_dir: str,
        config: ConversionConfig,
        task_id: str,
        calib_dataset_path: str | None = None,
        data_yaml_path: str | None = None,
    ) -> str:
        """PyTorch → TFLite 转换 (Ultralytics)"""
        import asyncio

        try:
            logger.info("加载 YOLO 模型", path=input_path)
            model = YOLO(input_path)

            imgsz = config.input_width
            int8 = config.quantization_type == "int8"

            export_kwargs = {
                "format": "tflite",
                "imgsz": imgsz,
                "int8": int8,
                "half": False,
                "dynamic": False,
                "simplify": True,
                "batch": 1,  # 减少批次大小以降低内存峰值
                "workers": 1,  # 单线程以减少内存开销
                # workspace 参数必须是数值(MB)，这里移除让 Ultralytics 使用默认值
            }

            # INT8 量化需要校准数据集
            if int8 and data_yaml_path and os.path.exists(data_yaml_path):
                export_kwargs["data"] = str(data_yaml_path)
                logger.info("使用用户 data.yaml 进行 INT8 量化", path=data_yaml_path)
            elif int8 and calib_dataset_path:
                # 自动生成 data.yaml
                auto_yaml = await self._generate_auto_data_yaml(
                    calib_path=calib_dataset_path,
                    work_dir=work_dir,
                    num_classes=config.num_classes,
                    class_names=config.class_names,
                )
                if auto_yaml:
                    export_kwargs["data"] = auto_yaml
                    logger.info("使用自动生成的 data.yaml", path=auto_yaml)
            else:
                logger.warning("INT8 量化未提供校准数据集，精度可能下降")

            # 关键修复：在线程池中执行 export，避免阻塞事件循环
            logger.info("开始 TFLite 导出（INT8量化，这可能需要几分钟）", imgsz=imgsz, int8=int8)
            export_path = await asyncio.to_thread(
                model.export,
                **export_kwargs
            )

            await self._update_progress(
                task_id,
                progress=30,
                current_step=f"TFLite export completed: {os.path.basename(str(export_path))}",
            )

            return str(export_path)

        except Exception as e:
            raise RuntimeError(f"PyTorch to TFLite conversion failed: {str(e)}")

    async def _generate_auto_data_yaml(
        self,
        calib_path: str,
        work_dir: str,
        num_classes: int,
        class_names: list[str],
    ) -> str | None:
        """自动生成 data.yaml（无用户提供时的降级方案）"""
        try:
            images_dir = self._find_images_dir(calib_path)
            names = class_names if class_names else [f"class_{i}" for i in range(num_classes)]

            yaml_data = {
                "path": calib_path,
                "train": os.path.relpath(images_dir, calib_path),
                "val": os.path.relpath(images_dir, calib_path),
                "nc": num_classes,
                "names": names,
            }

            output_path = os.path.join(work_dir, "data_auto.yaml")
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True)

            return output_path
        except Exception as e:
            logger.warning("Auto-generate data.yaml failed", error=str(e))
            return None

    async def _generate_network_bin(
        self,
        tflite_path: str,
        work_dir: str,
        config: ConversionConfig,
        task_id: str,
    ) -> str:
        """TFLite → network_rel.bin (调用 generate-reloc-model.sh with stedgeai)"""
        import asyncio

        try:
            output_path = os.path.join(work_dir, "network_rel.bin")

            # 检查 generate-reloc-model.sh 是否存在
            if not os.path.exists(self.generate_script):
                logger.warning(
                    "generate-reloc-model.sh 不存在，跳过 C 模型生成步骤",
                    path=self.generate_script,
                )
                # Fallback: 直接复制 tflite 作为 bin（用于调试）
                shutil.copy2(tflite_path, output_path)
                return output_path

            neural_art_config = f"{config.model_type.value.lower()}_od@neural_art_reloc.json"

            cmd = [
                "bash",
                self.generate_script,
                tflite_path,
                output_path,
                neural_art_config,
            ]

            logger.info("执行 C 模型生成", command=" ".join(cmd))

            # 获取包含 stedgeai PATH 的环境变量
            env = _get_stedgeai_env()

            # 使用异步 subprocess 避免阻塞事件循环
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=work_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=600
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError("C 模型生成超时（10分钟）")

            if process.returncode != 0:
                stderr_text = stderr.decode('utf-8', errors='replace')[-2000:]
                stdout_text = stdout.decode('utf-8', errors='replace')[-2000:]
                logger.error(
                    "C 模型生成失败",
                    returncode=process.returncode,
                    stderr=stderr_text,
                    stdout=stdout_text,
                )
                raise RuntimeError(f"C 模型生成失败 (exit {process.returncode}): {stderr_text[-500:]}")

            await self._update_progress(
                task_id, progress=60, current_step="C model generation completed ✓"
            )

            return output_path

        except Exception as e:
            logger.error("C 模型生成失败", error=str(e))
            raise

    async def _generate_config_json(
        self,
        work_dir: str,
        config: ConversionConfig,
        tflite_path: str,
    ) -> str:
        """生成模型配置 JSON 文件"""
        try:
            # 根据输入尺寸计算输出尺寸
            # YOLOv8 输出特征图: (input_size / stride)^2
            stride = 8
            output_height = config.input_height // stride
            output_width = config.input_width // stride

            config_json = {
                "model_name": config.model_name,
                "model_version": config.model_version,
                "input_spec": {
                    "width": config.input_width,
                    "height": config.input_height,
                    "channels": 3,
                    "data_type": config.input_data_type,
                    "color_format": config.color_format.value,
                    "normalization": {
                        "enabled": True,
                        "mean": config.mean,
                        "std": config.std,
                    },
                },
                "output_spec": {
                    "num_outputs": 1,
                    "outputs": [
                        {
                            "name": "output",
                            "batch": 1,
                            "height": output_height,
                            "width": output_width,
                            "channels": config.num_classes + 5,
                            "data_type": "int8" if config.quantization_type == "int8" else "float32",
                            "scale": 0.003921569,
                            "zero_point": 0,
                        }
                    ],
                },
                "postprocess_type": config.postprocess_type.value,
                "postprocess_params": {
                    "num_classes": config.num_classes,
                    "class_names": config.class_names or [f"class_{i}" for i in range(config.num_classes)],
                    "confidence_threshold": config.confidence_threshold,
                    "iou_threshold": config.iou_threshold,
                    "max_detections": config.max_detections,
                    "total_boxes": config.total_boxes,
                    "raw_output_scale": 0.003921569,
                    "raw_output_zero_point": 0,
                },
            }

            config_path = os.path.join(work_dir, "model_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_json, f, indent=2, ensure_ascii=False)

            logger.info("Configuration file generated successfully", path=config_path)
            return config_path

        except Exception as e:
            raise RuntimeError(f"配置文件生成失败: {str(e)}")

    async def _package_model(
        self,
        network_bin: str,
        config_json: str,
        config: ConversionConfig,
        work_dir: str,
    ) -> str:
        """打包最终 ZIP 文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{config.model_name}_{timestamp}.zip"
            output_path = os.path.join(settings.OUTPUT_DIR, output_filename)

            os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

            # 优先使用 model_packager.py
            if os.path.exists(self.packager_script):
                cmd = [
                    "python3",
                    self.packager_script,
                    "create",
                    "--model", network_bin,
                    "--config", config_json,
                    "--output", output_path,
                ]

                logger.info("执行模型打包", command=" ".join(cmd))

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=_get_stedgeai_env(),
                )

                if result.returncode != 0:
                    logger.warning(
                        "model_packager.py 失败，使用内置 ZIP 打包",
                        stderr=result.stderr[-500:],
                    )
                    # 降级方案
                    self._create_zip_package(network_bin, config_json, output_path, config)
                else:
                    logger.info("model_packager.py packaging succeeded")
            else:
                # 内置 ZIP 打包
                logger.info("Using built-in ZIP packaging (model_packager.py not found)")
                self._create_zip_package(network_bin, config_json, output_path, config)

            return output_filename

        except subprocess.TimeoutExpired:
            raise RuntimeError("模型打包超时（5分钟）")
        except Exception as e:
            raise RuntimeError(f"模型打包失败: {str(e)}")

    def _create_zip_package(
        self,
        network_bin: str,
        config_json: str,
        output_path: str,
        config: ConversionConfig,
    ) -> None:
        """内置 ZIP 打包方案"""
        model_name = config.model_name
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(network_bin):
                zf.write(network_bin, f"{model_name}/network_rel.bin")
            if os.path.exists(config_json):
                zf.write(config_json, f"{model_name}/model_config.json")
        logger.info("Built-in ZIP packaging completed", output_path=output_path)

    async def _update_progress(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        progress: int | None = None,
        current_step: str | None = None,
        error: str | None = None,
        output_filename: str | None = None,
    ) -> None:
        """更新任务进度"""
        from app.services.task_manager import TaskManager

        task_manager = TaskManager()
        await task_manager.update_task(
            task_id=task_id,
            status=status,
            progress=progress,
            current_step=current_step,
            error_message=error,
            output_filename=output_filename,
        )

    def get_presets(self) -> list[dict]:
        """获取配置预设列表"""
        return [
            {
                "id": "yolov8n-256",
                "name": "YOLOv8n 256x256",
                "description": "快速轻量检测模型",
            },
            {
                "id": "yolov8n-480",
                "name": "YOLOv8n 480x480",
                "description": "平衡精度和性能",
            },
            {
                "id": "yolov8n-640",
                "name": "YOLOv8n 640x640",
                "description": "高精度检测模型",
            },
        ]
