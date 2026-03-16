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
import queue
import time
import json
import os
import shutil
import yaml
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List
from functools import lru_cache

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
            return False, "Docker client not initialized"

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

    def _get_host_path(self, container_path: Path) -> Optional[str]:
        """获取宿主机路径（4级回退机制 + 缓存优化）

        参考 AIToolStack 的实现，确保 Docker-in-Docker 场景下正确映射路径

        Args:
            container_path: 容器内路径

        Returns:
            宿主机路径，如果获取失败则返回 None
        """
        import subprocess
        import json

        container_path_str = str(container_path)

        # 优先检查缓存
        with DockerToolChainAdapter._path_cache_lock:
            if container_path_str in DockerToolChainAdapter._path_cache:
                cached_path = DockerToolChainAdapter._path_cache[container_path_str]
                # 验证缓存路径是否仍然有效
                if Path(cached_path).exists():
                    logger.debug(f"✓ 使用缓存的宿主机路径: {cached_path}")
                    return cached_path
                else:
                    # 缓存失效，移除
                    del DockerToolChainAdapter._path_cache[container_path_str]

        # 优先级 1: 使用 docker inspect（最精确）
        container_name = os.environ.get("CONTAINER_NAME", "model-converter-api")
        try:
            inspect_cmd = [
                "docker", "inspect", container_name,
                "--format", "{{json .Mounts}}"
            ]
            result = subprocess.run(
                inspect_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                all_mounts = json.loads(result.stdout)
                for mount in all_mounts:
                    if mount.get("Destination") == container_path_str:
                        host_path = mount.get("Source")
                        logger.info(f"✓ Got host path from docker inspect: {host_path}")
                        # 缓存结果
                        with DockerToolChainAdapter._path_cache_lock:
                            DockerToolChainAdapter._path_cache[container_path_str] = host_path
                        return host_path
        except Exception as e:
            logger.warning(f"docker inspect failed: {e}")

        # 优先级 2: 从其他挂载点推断
        try:
            inspect_cmd = [
                "docker", "inspect", container_name,
                "--format", "{{json .Mounts}}"
            ]
            result = subprocess.run(
                inspect_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                all_mounts = json.loads(result.stdout)
                for mount in all_mounts:
                    destination = mount.get("Destination")
                    if destination in ["/app/uploads", "/app/outputs"]:
                        # 从 uploads 或 outputs 推断项目根目录
                        source = Path(mount.get("Source"))
                        project_root = source.parent.parent
                        inferred_path = project_root / "ne301"
                        if inferred_path.exists():
                            logger.info(f"✓ Inferred host path: {inferred_path}")
                            # 缓存结果
                            with DockerToolChainAdapter._path_cache_lock:
                                DockerToolChainAdapter._path_cache[container_path_str] = str(inferred_path)
                            return str(inferred_path)
        except Exception as e:
            logger.warning(f"Path inference failed: {e}")

        # 优先级 3: 从 /proc/mounts 读取
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == container_path_str:
                        host_path = parts[0]
                        logger.info(f"✓ Got host path from /proc/mounts: {host_path}")
                        return host_path
        except Exception as e:
            logger.warning(f"Failed to read /proc/mounts: {e}")

        # 优先级 4: 使用环境变量（最后手段）
        host_path = os.environ.get("NE301_HOST_PATH")
        if host_path:
            logger.info(f"✓ Got host path from env var: {host_path}")
            return host_path

        logger.error(f"✗ Failed to get host path for: {container_path_str}")
        return None

    def convert_model(
        self,
        task_id: str,
        model_path: str,
        config: Dict[str, Any],
        calib_dataset_path: Optional[str] = None,
        yaml_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """完整转换流程：PyTorch → TFLite → 量化 TFLite → NE301 .bin（优化版）

        集成缓存机制和性能监控

        Args:
            task_id: 任务 ID
            model_path: PyTorch 模型路径
            config: 转换配置
            calib_dataset_path: 校准数据集路径
            yaml_path: YAML 文件路径
            progress_callback: 进度回调函数

        Returns:
            NE301 .bin 文件路径
        """
        if not self.client:
            raise RuntimeError("Docker client not available")

        # 获取任务管理器用于推送日志
        task_manager = get_task_manager()

        logger.info(f"开始任务 {task_id} 的转换流程")
        task_manager.add_log(task_id, "开始模型转换流程...")

        # 开始性能监控
        self.performance_monitor.start_task(task_id)

        try:
            # 执行完整转换流程
            task_manager.add_log(task_id, f"模型文件: {Path(model_path).name}")
            task_manager.add_log(task_id, f"输入尺寸: {config['input_size']}x{config['input_size']}")

            model_size = Path(model_path).stat().st_size if Path(model_path).exists() else 0

            # ✅ 步骤 1+2: PyTorch → 量化 TFLite (0-60%) - 使用直接导出方法
            task_manager.add_log(task_id, "步骤 1/3: 导出量化 TFLite 模型")
            with self.performance_monitor.measure_step(task_id, "export_quantized_tflite"):
                if progress_callback:
                    progress_callback(10, "正在导出量化 TFLite 模型...")

                quantized_tflite = self._export_to_quantized_tflite(
                    model_path,
                    config["input_size"],
                    calib_dataset_path,
                    config
                )
                logger.info(f"✅ 量化 TFLite 导出成功: {quantized_tflite}")
                task_manager.add_log(task_id, f"✅ 量化 TFLite 导出完成: {Path(quantized_tflite).name}")

            # 步骤 3: 准备 NE301 项目 (60-70%)
            task_manager.add_log(task_id, "步骤 2/3: 准备 NE301 项目")
            with self.performance_monitor.measure_step(task_id, "prepare_ne301"):
                if progress_callback:
                    progress_callback(70, "正在准备 NE301 项目...")

                ne301_project = self._prepare_ne301_project(
                    task_id,
                    quantized_tflite,
                    config,
                    yaml_path
                )
                task_manager.add_log(task_id, "✅ NE301 项目准备完成")

            # 步骤 4: NE301 打包 (70-100%)
            task_manager.add_log(task_id, "步骤 3/3: NE301 打包")
            with self.performance_monitor.measure_step(task_id, "build_ne301"):
                if progress_callback:
                    progress_callback(75, "正在生成 NE301 部署包...")

                bin_path = self._build_ne301_model(
                    task_id,
                    ne301_project,
                    quantized_tflite  # ✅ 传递量化文件路径作为备选
                )

            if progress_callback:
                progress_callback(100, "转换完成!")

            # 结束性能监控
            output_size = Path(bin_path).stat().st_size if Path(bin_path).exists() else 0
            self.performance_monitor.end_task(
                task_id,
                success=True,
                model_size=model_size,
                output_size=output_size
            )

            task_manager.add_log(task_id, "✅ 转换完成!")
            task_manager.add_log(task_id, f"输出文件: {Path(bin_path).name}")
            logger.info(f"✅ 转换成功: {bin_path}")
            return bin_path

        except Exception as e:
            logger.error(f"转换失败: {e}")
            task_manager.add_log(task_id, f"❌ 转换失败: {str(e)}")
            # 记录失败
            self.performance_monitor.end_task(task_id, success=False)
            raise

    def _export_to_quantized_tflite(
        self,
        model_path: str,
        input_size: int,
        calib_dataset_path: Optional[str],
        config: Dict[str, Any]
    ) -> str:
        """步骤 1+2: PyTorch → 量化 TFLite（推荐方法）

        直接使用 YOLOv8 的 int8 量化导出，跳过 SavedModel 步骤
        避免输出形状错误问题（SavedModel 会输出 8400 boxes 而不是 1344）

        Args:
            model_path: PyTorch 模型路径
            input_size: 模型输入尺寸
            calib_dataset_path: 校准数据集路径（可选）
            config: 转换配置

        Returns:
            str: 量化后的 TFLite 文件路径
        """
        from ultralytics import YOLO
        import tensorflow as tf
        import tempfile

        logger.info(f"步骤 1+2: 直接导出量化 TFLite（推荐方法）")
        logger.info(f"  模型: {model_path}")
        logger.info(f"  输入尺寸: {input_size}x{input_size}")
        logger.info(f"  量化类型: int8")

        # 处理校准数据集
        actual_calib_path = calib_dataset_path
        if calib_dataset_path and calib_dataset_path.endswith('.zip'):
            logger.info(f"检测到校准数据集是 ZIP 文件，正在解压...")
            import zipfile

            extract_dir = tempfile.mkdtemp(prefix="calibration_")

            try:
                with zipfile.ZipFile(calib_dataset_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                logger.info(f"✅ 校准数据集已解压到: {extract_dir}")

                # 查找解压后的目录
                for root, dirs, files in os.walk(extract_dir):
                    image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    if image_files:
                        actual_calib_path = root
                        logger.info(f"✅ 找到校准图片目录: {actual_calib_path} (包含 {len(image_files)} 张图片)")
                        break

                if not actual_calib_path or actual_calib_path == calib_dataset_path:
                    logger.warning(f"解压后未找到有效的校准图片，将使用空路径")
                    actual_calib_path = extract_dir
            except Exception as e:
                logger.error(f"解压校准数据集失败: {e}")
                raise RuntimeError(f"解压校准数据集失败: {e}")

        # 加载 YOLOv8 模型
        model = YOLO(model_path)

        # ✅ 直接导出量化 TFLite
        export_args = {
            "format": "tflite",
            "imgsz": input_size,
            "int8": True,  # int8 量化
        }

        # 如果有校准数据集，传递 data 参数
        if actual_calib_path and Path(actual_calib_path).exists():
            export_args["data"] = actual_calib_path
            logger.info(f"  使用校准数据集: {actual_calib_path}")
        else:
            logger.info(f"  无校准数据集，使用 fake quantization")

        # 执行导出
        tflite_path = model.export(**export_args)

        # 验证输出形状
        logger.info(f"✅ 量化 TFLite 导出成功: {tflite_path}")

        try:
            interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
            output_details = interpreter.get_output_details()[0]
            output_shape = output_details['shape']

            logger.info(f"  输出形状: {output_shape}")

            # 计算预期的 total_boxes
            expected_boxes = {
                256: 1344,  # 3 * (32*32 + 16*16 + 8*8)
                320: 2100,
                416: 3549,
                512: 5376,
                640: 8400,
            }

            expected = expected_boxes.get(input_size)
            if expected:
                actual_boxes = output_shape[2] if len(output_shape) > 2 else output_shape[1]

                if actual_boxes == expected:
                    logger.info(f"✅ 输出形状正确: {output_shape} (total_boxes={actual_boxes})")
                else:
                    logger.error(f"❌ 输出形状错误！")
                    logger.error(f"  预期: (1, 34, {expected})")
                    logger.error(f"  实际: {output_shape}")
                    raise ValueError(
                        f"输出形状错误: {output_shape} != (1, 34, {expected})。"
                        f"这会导致固件大小过大。"
                    )
            else:
                logger.warning(f"无法验证输出形状（未知输入尺寸: {input_size}）")

        except Exception as e:
            logger.warning(f"⚠️  无法验证输出形状: {e}")
            logger.warning("继续处理，但建议手动检查 TFLite 模型输出")

        return str(tflite_path)

    def _prepare_ne301_project(
        self,
        task_id: str,
        quantized_tflite: str,
        config: Dict[str, Any],
        yaml_path: Optional[str] = None
    ) -> Path:
        """步骤 3: 准备 NE301 项目目录（改进版 - 完整 JSON 配置）

        参考 AIToolStack 的 ne301_export.py
        使用 generate_ne301_json_config() 生成完整配置
        """
        logger.info("步骤 3: 准备 NE301 项目")

        # 确保 NE301 项目目录存在
        ne301_project = self.ne301_project_path
        ne301_project.mkdir(parents=True, exist_ok=True)

        # 创建 Model 目录结构
        model_dir = ne301_project / "Model" / "weights"
        model_dir.mkdir(parents=True, exist_ok=True)

        # 复制 TFLite 模型
        model_name = f"model_{task_id}"
        tflite_target = model_dir / f"{model_name}.tflite"
        shutil.copy2(quantized_tflite, tflite_target)

        # 从 YAML 文件读取 class_names（如果提供）
        class_names: List[str] = []
        if yaml_path and Path(yaml_path).exists():
            try:
                with open(yaml_path, 'r') as f:
                    yaml_data = yaml.safe_load(f)

                # 从 YAML 中提取 class names
                if 'classes' in yaml_data:
                    class_names = [cls['name'] for cls in yaml_data['classes']]
                    logger.info(f"✅ 从 YAML 文件读取到 {len(class_names)} 个类别")
            except Exception as e:
                logger.warning(f"⚠️  读取 YAML 文件失败: {e}，将使用空类别列表")

        # ✅ 使用 AIToolStack 风格的完整 JSON 配置
        json_config = generate_ne301_json_config(
            tflite_path=Path(quantized_tflite),
            model_name=model_name,
            input_size=config["input_size"],
            num_classes=config["num_classes"],
            class_names=class_names,
            confidence_threshold=config.get("confidence_threshold", 0.25),
        )

        # ✅ 调试日志：验证 JSON 配置完整性
        config_size = len(json.dumps(json_config, indent=2))
        logger.info(f"📊 生成的 JSON 配置大小: {config_size} 字节")

        if config_size < 1000:
            logger.warning(f"⚠️  JSON 配置过小，可能不完整")
            logger.debug(f"JSON 配置内容:\n{json.dumps(json_config, indent=2)}")
        else:
            logger.info(f"✅ JSON 配置大小正常（完整配置）")

        # 写入 JSON 配置
        json_file = model_dir / f"{model_name}.json"
        with open(json_file, "w") as f:
            json.dump(json_config, f, indent=2)

        # ✅ 验证文件写入
        file_size = json_file.stat().st_size
        logger.info(f"✅ JSON 文件已写入: {json_file} ({file_size} 字节)")

        if file_size < 1000:
            logger.warning(f"⚠️  JSON 文件过小，请检查配置生成逻辑")

        # ✅ 更新 Makefile 中的 MODEL_NAME
        self._update_model_makefile(model_name)

        # 返回 Model 目录路径（不是 workspace 根目录）
        model_project_dir = ne301_project / "Model"
        logger.info(f"✅ NE301 项目准备完成: {model_project_dir}")
        logger.info(f"✅ JSON 配置文件: {json_file}")
        return model_project_dir

    def _build_ne301_model(
        self,
        task_id: str,
        ne301_project_path: Path,
        quantized_tflite: str
    ) -> str:
        """步骤 4: 调用 NE301 容器打包（改进版 - 架构感知）

        参考 AIToolStack 的 _build_with_docker() 实现
        支持在 ARM64 环境下通过 QEMU 模拟执行 NE301 打包

        Args:
            task_id: 任务 ID
            ne301_project_path: NE301 项目路径
            quantized_tflite: 量化 TFLite 文件路径（备选输出）

        Returns:
            NE301 .bin 文件路径 或 量化 TFLite 文件路径

        Raises:
            RuntimeError: 如果打包失败且备选输出也不可用
        """
        logger.info(f"步骤 4: 调用 NE301 容器打包")

        # 检测主机架构（仅用于日志记录）
        import platform
        host_arch = platform.machine()
        is_arm64 = host_arch.lower() in ('arm64', 'aarch64')

        if is_arm64:
            logger.info(f"ℹ️  检测到 ARM64 架构（Apple Silicon）")
            logger.info(f"ℹ️  将使用 QEMU 模拟执行 NE301 打包")
            logger.info(f"ℹ️  首次运行可能较慢，后续会缓存翻译结果")
        else:
            logger.info(f"ℹ️  检测到 x86_64 架构，将使用原生性能执行")

        # 尝试 NE301 打包（无论架构如何）
        try:
            return self._attempt_ne301_build(task_id, ne301_project_path, quantized_tflite)
        except RuntimeError as e:
            logger.error(f"❌ NE301 打包失败: {e}")
            logger.info("📦 提供量化 TFLite 作为备选输出...")
            return self._provide_quantized_tflite_output(task_id, quantized_tflite)

    def _attempt_ne301_build(
        self,
        task_id: str,
        ne301_project_path: Path,
        quantized_tflite: str
    ) -> str:
        """尝试 NE301 打包（支持版本检测和动态适配）

        Args:
            task_id: 任务 ID
            ne301_project_path: NE301 项目路径
            quantized_tflite: 量化 TFLite 文件路径

        Returns:
            最终输出文件路径（.bin 或 .tflite）

        Raises:
            RuntimeError: 如果所有打包方式都失败
        """
        logger.info("📦 NE301 打包流程")
        logger.info(f"  项目路径: {ne301_project_path}")

        # 🔍 步骤1: 检测工具链版本和可用工具
        # 注意：工具链检测需要使用 SDK 根目录（不是 Model 子目录）
        sdk_root = self.ne301_project_path
        toolchain = get_ne301_toolchain(sdk_root)

        # 🔍 步骤2: 确定最佳打包方式
        packaging_method = toolchain.get_best_packaging_method()
        logger.info(f"  选择打包方式: {packaging_method}")

        try:
            # 执行对应的打包流程
            if packaging_method == 'ota':
                return self._build_ota_package(task_id, ne301_project_path, toolchain)
            elif packaging_method == 'model':
                return self._build_model_package(task_id, ne301_project_path, toolchain)
            else:
                return self._provide_fallback_output(task_id, quantized_tflite)

        except Exception as e:
            logger.error(f"❌ {packaging_method} 打包失败: {e}")
            logger.info("📦 降级到 TFLite 输出...")
            return self._provide_fallback_output(task_id, quantized_tflite)

    def _build_ota_package(
        self,
        task_id: str,
        ne301_project_path: Path,
        toolchain
    ) -> str:
        """OTA 固件打包（推荐方式）

        生成带 OTA 头部的完整固件，兼容设备升级
        """
        logger.info("🎯 使用 OTA 固件打包（推荐）")

        # 执行 make pkg-model（已经包含 OTA header）
        pkg_bin_path = self._make_model(task_id, ne301_project_path)

        # pkg-model 已经生成了带 OTA header 的固件，直接返回
        logger.info(f"✅ OTA 固件已生成: {pkg_bin_path.name}")
        return str(pkg_bin_path)

    def _build_model_package(
        self,
        task_id: str,
        ne301_project_path: Path,
        toolchain
    ) -> str:
        """纯模型打包（备用方式）

        生成 NE301 模型包，不带 OTA 头部
        """
        logger.info("🎯 使用纯模型打包（备用）")

        # 执行 make model
        model_bin_path = self._make_model(task_id, ne301_project_path)

        # 直接返回模型包
        return model_bin_path

    def _make_model(self, task_id: str, ne301_project_path: Path) -> Path:
        """启动 NE301 容器执行 make 命令"""
        import os

        logger.info(f"  项目路径: {ne301_project_path}")
        logger.info(f"  使用 NE301 镜像: {self.ne301_image}")

        # 关键修复：NE301 镜像的工作目录是 /workspace，所以挂载命名卷到 /workspace
        # 而不是子目录 /workspace/ne301
        volumes = {
            "ne301_workspace": {"bind": "/workspace", "mode": "rw"}
        }

        # 创建临时容器名
        container_name = "ne301-builder-" + os.urandom(4).hex()

        # 关键修复：make pkg-model 必须在 SDK 根目录执行
        # 需要设置环境变量并加载 ST Edge AI 环境
        # 使用 bash -l 来确保加载 /etc/profile.d/ 中的脚本
        make_cmd = "bash -lc 'cd /workspace && make pkg-model'"

        logger.info(f"  启动 NE301 容器: {container_name}")
        logger.info(f"  执行命令: {make_cmd}")
        logger.info(f"  挂载卷: ne301_workspace -> /workspace")

        container = None
        output_bin = None
        try:
            # 启动临时容器执行 make（不自动删除，以便获取日志）
            container = self.client.containers.run(
                self.ne301_image,
                command=["bash", "-c", make_cmd],
                volumes=volumes,
                name=container_name,
                auto_remove=False,  # 不自动删除，手动管理
                detach=True,
                network="model-converter_conversion_network"  # 完整网络名称
            )

            logger.info(f"  ✓ NE301 容器已启动: {container.id[:12]}")

            # 等待容器执行完成
            result = container.wait(timeout=300)  # 5分钟超时

            # 获取容器日志（在容器删除之前）
            try:
                logs = container.logs(tail=100).decode("utf-8")
                if logs:
                    logger.debug(f"  容器日志:\n{logs}")
            except Exception as e:
                logger.warning(f"  获取容器日志失败: {e}")
            # 检查输出文件是否生成
            # pkg-model 生成文件名格式：ne301_Model_v{version}_pkg.bin
            # 文件在 SDK 根目录的 build/ 目录，不是 Model/build/
            build_dir = self.ne301_project_path / "build"
            pkg_files = sorted(
                build_dir.glob("ne301_Model_v*_pkg.bin"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if pkg_files:
                output_bin = pkg_files[0]  # 最新的文件
                file_size = output_bin.stat().st_size
                logger.info(f"  ✓ make pkg-model 完成，输出文件: {output_bin.name} ({file_size:,} bytes)")
                # 退出码非零但文件存在，可能是 QEMU 模拟问题
                if result["StatusCode"] != 0:
                    logger.warning(f"  ⚠️  容器退出码: {result['StatusCode']}（可能为 QEMU 模拟问题，但输出文件有效）")
            else:
                logger.error(f"  ✗ make 失败，退出码: {result['StatusCode']}，输出文件不存在")
                raise RuntimeError(f"make pkg-model 失败: exit code {result['StatusCode']}, 输出文件未生成")

        finally:
            # 手动删除容器
            if container:
                try:
                    container.remove(force=True)
                    logger.info(f"  ✓ 容器已清理: {container_name}")
                except Exception as e:
                    logger.warning(f"  清理容器失败（可能已删除）: {e}")

        return output_bin

    def _run_make_directly(self, ne301_project_path: Path) -> None:
        """直接执行 make（在容器内）"""
        import subprocess

        try:
            result = subprocess.run(
                ["make", "model"],
                cwd=str(ne301_project_path),
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )

            if result.returncode != 0:
                logger.error(f"make 失败: {result.stderr}")
                raise RuntimeError(f"make model 失败: {result.stderr}")

            logger.info("✅ make model 完成")
            if result.stdout:
                logger.debug(f"make 输出: {result.stdout[-500:]}")  # 只显示最后500字符

        except subprocess.TimeoutExpired:
            raise RuntimeError("make model 超时（>120秒）")

    def _run_make_in_container(self, ne301_project_path: Path) -> None:
        """在 NE301 容器中执行 make"""
        # 检查 NE301 容器是否运行
        try:
            ne301_container = self.client.containers.get("ne301-dev")
        except Exception:
            # 如果容器不存在，尝试创建临时容器
            logger.info("创建临时 NE301 容器...")
            ne301_container = self._run_temp_ne301_container(ne301_project_path)

        # 执行 make
        try:
            exit_code, output = ne301_container.exec_run(
                f"bash -c 'cd {ne301_project_path} && make model'",
                workdir=str(ne301_project_path)
            )

            if exit_code != 0:
                logger.error(f"make 失败: {output.decode('utf-8')[-500:]}")
                raise RuntimeError(f"make model 失败: exit code {exit_code}")

            logger.info("✅ make model 完成")

        except Exception as e:
            logger.error(f"执行 make 失败: {e}")
            raise

    def _run_temp_ne301_container(self, ne301_project_path: Path):
        """创建临时 NE301 容器"""
        import tempfile

        # 创建卷挂载
        volumes = {
            str(ne301_project_path): {"bind": str(ne301_project_path), "mode": "rw"}
        }

        # 运行容器（自动删除）
        container = self.client.containers.run(
            self.ne301_image,
            command="tail -f /dev/null",  # 保持容器运行
            volumes=volumes,
            detach=True,
            auto_remove=True,
            name=f"ne301-tmp-{id(self)}"
        )

        return container

    def _add_ota_header(
        self,
        task_id: str,
        ne301_project_path: Path,
        toolchain,
        model_bin_path: Path
    ) -> str:
        """添加 OTA 固件头部"""
        logger.info("步骤 2: 添加 OTA 固件头部...")

        # 获取版本号
        version = toolchain.get_model_version()
        ota_version_str = '.'.join(map(str, version.to_tuple()))

        # 获取 OTA 打包工具
        ota_packer = toolchain.get_ota_packager()
        if not ota_packer:
            raise RuntimeError("OTA 打包工具不可用")

        # 输出路径
        filename = toolchain.get_package_name(task_id, 'ota')
        ota_pkg_path = ne301_project_path / "build" / f"{filename}.bin"

        # 构造命令
        cmd = [
            "python3",
            str(ota_packer),
            str(model_bin_path),
            "-o", str(ota_pkg_path),
            "-t", "ai_model",
            "-n", "NE301_MODEL",
            "-d", "NE301 AI Model",
            "-v", ota_version_str
        ]

        logger.info(f"  版本: {version}")
        logger.info(f"  输出: {ota_pkg_path.name}")

        # 执行打包
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ne301_project_path)
        )

        output = []
        for line in process.stdout:
            line = line.strip()
            output.append(line)
            logger.info(f"[OTA Packer] {line}")

        process.wait(timeout=60)

        if process.returncode != 0:
            raise RuntimeError(f"OTA 打包失败: {' '.join(output[-10:])}")

        # 复制到输出目录
        output_dir = Path("/app/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_path = output_dir / ota_pkg_path.name
        shutil.copy2(ota_pkg_path, final_path)

        logger.info(f"✅ OTA 固件生成成功: {final_path}")
        return str(final_path)

    def _provide_fallback_output(self, task_id: str, quantized_tflite: str) -> str:
        """提供降级输出（TFLite）"""
        logger.info("⚠️  降级到 TFLite 输出")

        output_dir = Path("/app/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        fallback_path = output_dir / f"quantized_model_{task_id}.tflite"
        shutil.copy2(quantized_tflite, fallback_path)

        logger.info(f"✅ TFLite 文件已提供: {fallback_path}")
        logger.warning("⚠️  注意: TFLite 格式需要手动打包为 NE301 格式")

        return str(fallback_path)
        """尝试 NE301 打包（仅在 x86_64 环境）

        Args:
            task_id: 任务 ID
            ne301_project_path: NE301 项目路径
            quantized_tflite: 量化 TFLite 文件路径

        Returns:
            NE301 .bin 文件路径

        Raises:
            RuntimeError: 如果打包失败
        """
        model_name = f"model_{task_id}"

        # ✅ 获取宿主机路径（关键改进）
        host_path = self._get_host_path(Path("/workspace/ne301"))

        if not host_path:
            raise RuntimeError(
                "❌ 无法获取宿主机路径！\n"
                "请检查：\n"
                "1. docker-compose.yml 中是否配置了 ./ne301:/workspace/ne301\n"
                f"2. CONTAINER_NAME 环境变量是否正确（当前: {os.environ.get('CONTAINER_NAME', '未设置')}）\n"
                "3. Docker 套接字是否正确挂载\n"
                "调试命令：docker inspect model-converter-api | jq '.[0].Mounts'"
            )

        logger.info(f"✓ 使用宿主机路径: {host_path}")

        # 构造 Docker 命令（使用宿主机路径）
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{host_path}:/workspace/ne301",  # ✅ 宿主机路径
            "-w", "/workspace/ne301",
            self.ne301_image,
            "bash", "-c",
            f"cd /workspace/ne301 && "
            f"if [ ! -f Model/weights/{model_name}.tflite ]; then "
            f"  echo '❌ Model file not found'; exit 1; "
            f"fi && "
            f"echo '✓ Starting NE301 build...' && "
            f"make model && "
            f"make pkg-model && "
            f"echo '✓ Package created'"
        ]

        logger.info(f"执行 NE301 打包命令...")

        # 执行命令并实时输出日志
        process = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # 实时输出日志
        output_lines = []
        for line in process.stdout:
            line = line.strip()
            output_lines.append(line)
            logger.info(f"[NE301] {line}")

        process.wait(timeout=600)

        if process.returncode != 0:
            error_output = "\n".join(output_lines[-50:])  # 最后 50 行
            raise RuntimeError(f"❌ NE301 打包失败:\n{error_output}")

        # ✅ 步骤4.1: 查找生成的模型包
        model_bin_path = ne301_project_path / "build" / "ne301_Model.bin"
        if not model_bin_path.exists():
            raise FileNotFoundError(f"❌ NE301 模型文件未生成: {model_bin_path}")

        logger.info(f"✅ 模型包已生成: {model_bin_path}")

        # ✅ 步骤4.2: 添加 OTA 固件头部
        logger.info("步骤 4.2: 添加 OTA 固件头部...")

        # 版本号格式: major.minor.patch.build
        # 使用 git commit count 作为 build number，或使用时间戳
        import time
        build_number = int(time.time()) % 10000  # 0-9999
        ota_version = "2.0.0.{}".format(build_number)

        # OTA 固件输出路径
        ota_pkg_path = ne301_project_path / "build" / f"ne301_Model_v{ota_version}_pkg.bin"

        # 调用 ota_packer.py 添加 OTA 头部
        ota_packer_script = ne301_project_path / "Script" / "ota_packer.py"
        if not ota_packer_script.exists():
            logger.warning(f"⚠️  OTA 打包工具不存在: {ota_packer_script}")
            logger.info("使用原始模型包作为备选")
            final_bin_path = model_bin_path
        else:
            # 构造 OTA 打包命令
            ota_pack_cmd = [
                "python3",
                str(ota_packer_script),
                str(model_bin_path),
                "-o", str(ota_pkg_path),
                "-t", "ai_model",
                "-n", "NE301_MODEL",
                "-d", "NE301 AI Model",
                "-v", ota_version
            ]

            logger.info(f"执行 OTA 打包命令...")
            logger.info(f"  版本: {ota_version}")

            # 执行打包
            pack_process = subprocess.Popen(
                ota_pack_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 实时输出日志
            pack_output = []
            for line in pack_process.stdout:
                line = line.strip()
                pack_output.append(line)
                logger.info(f"[OTA Packer] {line}")

            pack_process.wait(timeout=60)

            if pack_process.returncode != 0:
                logger.warning(f"⚠️  OTA 打包失败，使用原始模型包")
                final_bin_path = model_bin_path
            else:
                logger.info(f"✅ OTA 固件生成成功: {ota_pkg_path}")
                final_bin_path = ota_pkg_path

        # ✅ 步骤4.3: 复制到输出目录
        output_dir = Path("/app/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_output_path = output_dir / final_bin_path.name
        shutil.copy2(final_bin_path, final_output_path)

        logger.info(f"✅ NE301 打包成功: {final_output_path}")
        return str(final_output_path)

    def _update_model_makefile(self, model_name: str) -> None:
        """更新 Model/Makefile 中的 MODEL_NAME 变量

        Args:
            model_name: 模型名称（不含扩展名）
        """
        import re

        makefile_path = self.ne301_project_path / "Model" / "Makefile"

        if not makefile_path.exists():
            logger.warning(f"⚠️  Makefile 不存在: {makefile_path}")
            return

        try:
            # 读取 Makefile 内容
            with open(makefile_path, 'r') as f:
                content = f.read()

            # 替换 MODEL_NAME 行
            pattern = r'^MODEL_NAME\s*=\s*.+$'
            replacement = f'MODEL_NAME = {model_name}'

            new_content = re.sub(
                pattern,
                replacement,
                content,
                flags=re.MULTILINE
            )

            # 写回 Makefile
            with open(makefile_path, 'w') as f:
                f.write(new_content)

            logger.info(f"✅ Makefile 已更新: MODEL_NAME = {model_name}")

        except Exception as e:
            logger.error(f"❌ 更新 Makefile 失败: {e}")
            # 不中断流程，继续执行

    def _provide_quantized_tflite_output(
        self,
        task_id: str,
        quantized_tflite: str
    ) -> str:
        """提供量化 TFLite 文件作为备选输出

        Args:
            task_id: 任务 ID
            quantized_tflite: 量化 TFLite 文件路径

        Returns:
            量化 TFLite 文件路径（在输出目录中）
        """
        logger.info("📦 准备量化 TFLite 输出...")

        # 检查量化文件是否存在
        tflite_path = Path(quantized_tflite)
        if not tflite_path.exists():
            raise FileNotFoundError(f"量化 TFLite 文件未找到: {quantized_tflite}")

        # 复制到输出目录
        output_dir = Path("/app/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        final_tflite_path = output_dir / f"quantized_model_{task_id}.tflite"
        shutil.copy2(tflite_path, final_tflite_path)

        logger.info(f"✅ 量化 TFLite 已生成: {final_tflite_path}")
        logger.warning("⚠️  注意：此文件为量化 TFLite 格式，不是 NE301 .bin 格式")
        logger.info("💡 提示：要在 x86_64 环境中完成 NE301 打包，请执行以下步骤：")
        logger.info("   1. 将量化 TFLite 文件传输到 x86_64 服务器")
        logger.info("   2. 在该服务器上运行 NE301 打包命令")
        logger.info("   3. 或使用云服务完成打包（AWS/GCP/Azure x86_64 实例）")

        return str(final_tflite_path)
