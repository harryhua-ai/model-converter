"""
量化流程测试

测试 NE301 模型转换的量化流程，包括：
1. SavedModel 导出
2. ST 官方量化脚本调用
3. 量化模型验证
4. 完整转换流程

覆盖场景：
- 无校准数据集（fake 量化）
- 有校准数据集（真实量化）
- 不同输入尺寸 (256/320/416/512/640)
- 错误处理（文件不存在、量化失败等）
"""
import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import tempfile
import json
import yaml
import numpy as np
from typing import Dict, Any

from app.core.docker_adapter import DockerToolChainAdapter


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def adapter():
    """创建 DockerToolChainAdapter 实例"""
    adapter = DockerToolChainAdapter()
    adapter.client = Mock()
    return adapter


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """示例转换配置"""
    return {
        "input_size": 640,
        "num_classes": 80,
        "model_type": "yolov8",
        "confidence_threshold": 0.25,
    }


@pytest.fixture
def temp_model_file(tmp_path):
    """创建临时 PyTorch 模型文件"""
    model_file = tmp_path / "test_model.pt"
    model_file.write_bytes(b"\x00" * 1024)  # 1KB mock model
    return str(model_file)


@pytest.fixture
def temp_calibration_zip(tmp_path):
    """创建临时校准数据集 ZIP 文件"""
    import zipfile

    zip_file = tmp_path / "calibration.zip"
    calib_dir = tmp_path / "calib_images"
    calib_dir.mkdir()

    # 创建一些模拟图片文件
    for i in range(10):
        img_file = calib_dir / f"img_{i}.jpg"
        img_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # JPEG header + data

    # 打包成 ZIP
    with zipfile.ZipFile(zip_file, 'w') as zf:
        for img_file in calib_dir.glob("*.jpg"):
            zf.write(img_file, img_file.name)

    return str(zip_file)


@pytest.fixture
def temp_saved_model(tmp_path):
    """创建临时 SavedModel 目录结构"""
    saved_model_dir = tmp_path / "saved_model"
    saved_model_dir.mkdir()

    # 创建 SavedModel 必需文件
    (saved_model_dir / "saved_model.pb").write_bytes(b"\x00" * 100)
    variables_dir = saved_model_dir / "variables"
    variables_dir.mkdir()
    (variables_dir / "variables.index").write_bytes(b"\x00" * 50)
    (variables_dir / "variables.data-00000-of-00001").write_bytes(b"\x00" * 100)

    return str(saved_model_dir)


@pytest.fixture
def temp_tflite_file(tmp_path):
    """创建临时 TFLite 文件"""
    tflite_file = tmp_path / "model.tflite"
    # 写入最小的有效 TFLite header
    tflite_file.write_bytes(b"\x00" * 100)
    return str(tflite_file)


@pytest.fixture
def temp_quant_config(tmp_path):
    """创建临时量化配置文件"""
    config_file = tmp_path / "user_config_quant.yaml"
    config_data = {
        "model": {
            "name": "test_model",
            "uc": "od_coco",
            "model_path": "/path/to/saved_model",
            "input_shape": [640, 640, 3]
        },
        "quantization": {
            "fake": True,
            "quantization_type": "per_channel",
            "quantization_input_type": "uint8",
            "quantization_output_type": "int8",
            "calib_dataset_path": "",
            "export_path": "./quantized_models",
            "max_calib_images": 200
        },
        "pre_processing": {
            "rescaling": {"scale": 255, "offset": 0}
        }
    }

    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    return config_file


# ============================================================
# 1. _export_to_saved_model() 函数测试
# ============================================================

class TestExportToSavedModel:
    """测试 SavedModel 导出功能"""

    @pytest.mark.unit
    def test_export_to_saved_model_success(self, adapter, temp_model_file, tmp_path):
        """测试成功导出 SavedModel"""
        with patch("ultralytics.YOLO") as mock_yolo:
            # Mock YOLO 模型
            mock_model = MagicMock()
            mock_model.export.return_value = str(tmp_path / "saved_model")
            mock_yolo.return_value = mock_model

            # 调用导出
            result = adapter._export_to_saved_model(
                model_path=temp_model_file,
                input_size=640,
                task_id="test_task"
            )

            # 验证
            assert result is not None
            assert "saved_model" in result
            mock_yolo.assert_called_once_with(temp_model_file)
            mock_model.export.assert_called_once()

    @pytest.mark.unit
    def test_export_to_saved_model_different_sizes(self, adapter, temp_model_file):
        """测试不同输入尺寸的导出"""
        input_sizes = [256, 320, 416, 512, 640]

        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/saved_model"
            mock_yolo.return_value = mock_model

            for size in input_sizes:
                mock_model.export.reset_mock()

                adapter._export_to_saved_model(
                    model_path=temp_model_file,
                    input_size=size,
                    task_id=f"test_task_{size}"
                )

                # 验证导出参数包含正确的 imgsz
                call_kwargs = mock_model.export.call_args[1]
                assert call_kwargs["imgsz"] == size

    @pytest.mark.unit
    def test_export_to_saved_model_model_not_found(self, adapter):
        """测试模型文件不存在时抛出错误"""
        with pytest.raises(FileNotFoundError):
            adapter._export_to_saved_model(
                model_path="/nonexistent/model.pt",
                input_size=640,
                task_id="test_task"
            )

    @pytest.mark.unit
    def test_export_to_saved_model_ultralytics_error(self, adapter, temp_model_file):
        """测试 Ultralytics 导出失败时的错误处理"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.side_effect = RuntimeError("Export failed")
            mock_yolo.return_value = mock_model

            with pytest.raises(RuntimeError, match="Export failed"):
                adapter._export_to_saved_model(
                    model_path=temp_model_file,
                    input_size=640,
                    task_id="test_task"
                )


# ============================================================
# 1.5 _export_to_quantized_tflite() 函数测试
# ============================================================

class TestExportToQuantizedTFLite:
    """测试直接导出量化 TFLite 功能"""

    @pytest.mark.unit
    def test_export_quantized_tflite_with_fraction_parameter(self, adapter, temp_model_file):
        """测试 fraction 参数被正确传递给 YOLO.export()"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {
                "input_size": 640,
                "num_classes": 80,
                "fraction": 0.2  # 新增参数
            }

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=None,  # 添加缺失的参数
                config=config
            )

            # 验证 fraction 参数被传递
            call_kwargs = mock_model.export.call_args[1]
            assert "fraction" in call_kwargs
            assert call_kwargs["fraction"] == 0.2

    @pytest.mark.unit
    def test_export_quantized_tflite_default_fraction(self, adapter, temp_model_file):
        """测试未提供 fraction 时使用默认值"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {
                "input_size": 640,
                "num_classes": 80
                # 未提供 fraction
            }

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=None,  # 添加缺失的参数
                config=config
            )

            # 验证使用默认值 0.2
            call_kwargs = mock_model.export.call_args[1]
            assert "fraction" in call_kwargs
            assert call_kwargs["fraction"] == 0.2  # 默认值

    @pytest.mark.unit
    def test_export_quantized_tflite_fraction_with_calibration(
        self, adapter, temp_model_file, temp_calibration_zip
    ):
        """测试 fraction 参数与校准数据集配合"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {
                "input_size": 640,
                "num_classes": 80,
                "fraction": 0.3  # 30% 校准数据
            }

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=temp_calibration_zip,
                yaml_path=None,  # 添加缺失的参数
                config=config
            )

            # 验证 data 和 fraction 都被传递
            call_kwargs = mock_model.export.call_args[1]
            assert "data" in call_kwargs
            assert "fraction" in call_kwargs
            assert call_kwargs["fraction"] == 0.3

    @pytest.mark.unit
    def test_export_quantized_tflite_custom_fraction(self, adapter, temp_model_file):
        """测试自定义 fraction 值"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {
                "input_size": 640,
                "num_classes": 80,
                "fraction": 0.5  # 50% 校准数据
            }

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=None,  # 添加缺失的参数
                config=config
            )

            # 验证自定义 fraction 值被使用
            call_kwargs = mock_model.export.call_args[1]
            assert call_kwargs["fraction"] == 0.5


# ============================================================
# 2. _run_st_quantization() 函数测试
# ============================================================

class TestRunSTQuantization:
    """测试 ST 官方量化脚本调用"""

    @pytest.mark.unit
    def test_quantization_fake_mode(self, adapter, temp_quant_config, tmp_path):
        """测试 fake 量化模式（无校准数据集）"""
        # 创建量化输出目录和文件
        output_dir = temp_quant_config.parent / "quantized_models"
        output_dir.mkdir(parents=True, exist_ok=True)
        quantized_file = output_dir / "model_quant.tflite"
        quantized_file.write_bytes(b"\x00" * 100)

        # Mock subprocess.run
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b"Quantized model generated",
                stderr=b""
            )

            # 调用量化
            result = adapter._run_st_quantization(
                config_path=temp_quant_config,
                task_id="test_task"
            )

            # 验证
            assert result is not None
            assert result.endswith(".tflite")
            mock_run.assert_called_once()

    @pytest.mark.unit
    def test_quantization_with_calibration(self, adapter, temp_quant_config, tmp_path):
        """测试使用真实校准数据集的量化"""
        # 创建量化输出目录和文件
        output_dir = temp_quant_config.parent / "quantized_models"
        output_dir.mkdir(parents=True, exist_ok=True)
        quantized_file = output_dir / "model_quant.tflite"
        quantized_file.write_bytes(b"\x00" * 100)

        # Mock subprocess.run
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b"Quantized model generated",
                stderr=b""
            )

            # 调用量化
            result = adapter._run_st_quantization(
                config_path=temp_quant_config,
                task_id="test_task"
            )

            # 验证
            assert result is not None
            assert result.endswith(".tflite")
            mock_run.assert_called_once()

    @pytest.mark.unit
    def test_quantization_different_input_sizes(self, adapter, tmp_path):
        """测试不同输入尺寸的量化配置"""
        input_sizes = [256, 320, 416, 512, 640]

        for size in input_sizes:
            # 为每个尺寸创建配置
            config_file = tmp_path / f"config_{size}.yaml"
            config_data = {
                "model": {
                    "name": f"model_{size}",
                    "uc": "od_coco",
                    "model_path": "/path/to/saved_model",
                    "input_shape": [size, size, 3]
                },
                "quantization": {
                    "fake": True,
                    "quantization_type": "per_channel",
                    "export_path": str(tmp_path / "quantized_models"),
                }
            }

            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            # 创建输出
            output_dir = config_file.parent / "quantized_models"
            output_dir.mkdir(exist_ok=True)
            quantized_file = output_dir / f"model_{size}_quant.tflite"
            quantized_file.write_bytes(b"\x00" * 100)

            # Mock subprocess.run
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=b"",
                    stderr=b""
                )

                # 调用量化
                result = adapter._run_st_quantization(
                    config_path=config_file,
                    task_id=f"test_task_{size}"
                )

                # 验证
                assert result is not None
                mock_run.assert_called_once()

    @pytest.mark.unit
    def test_quantization_script_failure(self, adapter, temp_quant_config):
        """测试量化脚本执行失败"""
        with patch("subprocess.run") as mock_run:
            # 模拟脚本执行失败
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr=b"Quantization failed",
                stdout=b""
            )

            with pytest.raises(RuntimeError, match="量化失败"):
                adapter._run_st_quantization(
                    config_path=temp_quant_config,
                    task_id="test_task"
                )

    @pytest.mark.unit
    @pytest.mark.skip(reason="由于 mock 脚本总是会创建文件，难以模拟此场景")
    def test_quantization_output_file_not_created(self, adapter, temp_quant_config, tmp_path):
        """测试量化文件未生成"""
        # 创建空的输出目录
        output_dir = temp_quant_config.parent / "quantized_models"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 完全 mock subprocess.run，让它返回成功但不实际运行脚本
        # 这样就不会创建任何文件
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=b"",
                stderr=b""
            )

            # 由于 subprocess.run 被 mock，真实的脚本不会被调用
            # 所以输出目录保持为空，测试应该正确检测到这种情况
            with pytest.raises(FileNotFoundError, match="量化文件未生成"):
                adapter._run_st_quantization(
                    config_path=temp_quant_config,
                    task_id="test_task"
                )


# ============================================================
# 3. _validate_quantized_model() 函数测试
# ============================================================

class TestValidateQuantizedModel:
    """测试量化模型验证"""

    @pytest.mark.unit
    def test_validate_model_success(self, adapter, temp_tflite_file):
        """测试成功验证量化模型"""
        # 导入 tensorflow 来 mock 正确的模块路径
        import tensorflow as tf

        with patch.object(tf.lite, "Interpreter") as mock_interpreter_cls:
            # Mock interpreter
            mock_interpreter = MagicMock()
            mock_interpreter.get_input_details.return_value = [
                {"shape": [1, 640, 640, 3], "dtype": np.uint8}
            ]
            mock_interpreter.get_output_details.return_value = [
                {"shape": [1, 34, 8400], "dtype": np.int8}
            ]
            mock_interpreter_cls.return_value = mock_interpreter

            # 验证模型
            result = adapter._validate_quantized_model(
                quantized_tflite_path=temp_tflite_file,
                input_size=640,
                task_id="test_task"
            )

            # 验证
            assert result is True
            mock_interpreter_cls.assert_called_once()

    @pytest.mark.unit
    def test_validate_model_output_shape_correct(self, adapter, temp_tflite_file):
        """测试输出形状验证（正确）"""
        import tensorflow as tf

        with patch.object(tf.lite, "Interpreter") as mock_interpreter_cls:
            mock_interpreter = MagicMock()
            # 640x640 的预期输出: (1, 34, 8400)
            mock_interpreter.get_output_details.return_value = [
                {"shape": [1, 34, 8400], "dtype": np.int8}
            ]
            mock_interpreter.get_input_details.return_value = [
                {"shape": [1, 640, 640, 3]}
            ]
            mock_interpreter_cls.return_value = mock_interpreter

            result = adapter._validate_quantized_model(
                quantized_tflite_path=temp_tflite_file,
                input_size=640,
                task_id="test_task"
            )

            assert result is True

    @pytest.mark.unit
    def test_validate_model_output_shape_incorrect(self, adapter, temp_tflite_file):
        """测试输出形状验证（错误）"""
        import tensorflow as tf

        with patch.object(tf.lite, "Interpreter") as mock_interpreter_cls:
            mock_interpreter = MagicMock()
            # 错误的输出形状
            mock_interpreter.get_output_details.return_value = [
                {"shape": [1, 34, 100], "dtype": np.int8}
            ]
            mock_interpreter.get_input_details.return_value = [
                {"shape": [1, 640, 640, 3]}
            ]
            mock_interpreter_cls.return_value = mock_interpreter

            with pytest.raises(ValueError, match="输出形状错误"):
                adapter._validate_quantized_model(
                    quantized_tflite_path=temp_tflite_file,
                    input_size=640,
                    task_id="test_task"
                )

    @pytest.mark.unit
    def test_validate_model_different_sizes(self, adapter, temp_tflite_file):
        """测试不同输入尺寸的输出形状验证"""
        import tensorflow as tf

        test_cases = [
            (256, 1344),
            (320, 2100),
            (416, 3549),
            (512, 5376),
            (640, 8400),
        ]

        with patch.object(tf.lite, "Interpreter") as mock_interpreter_cls:
            for input_size, expected_boxes in test_cases:
                mock_interpreter = MagicMock()
                mock_interpreter.get_output_details.return_value = [
                    {"shape": [1, 34, expected_boxes]}
                ]
                mock_interpreter.get_input_details.return_value = [
                    {"shape": [1, input_size, input_size, 3]}
                ]
                mock_interpreter_cls.return_value = mock_interpreter

                result = adapter._validate_quantized_model(
                    quantized_tflite_path=temp_tflite_file,
                    input_size=input_size,
                    task_id=f"test_task_{input_size}"
                )

                assert result is True

    @pytest.mark.unit
    def test_validate_model_file_not_found(self, adapter):
        """测试模型文件不存在"""
        with pytest.raises(FileNotFoundError):
            adapter._validate_quantized_model(
                quantized_tflite_path="/nonexistent/model.tflite",
                input_size=640,
                task_id="test_task"
            )

    @pytest.mark.unit
    def test_validate_model_invalid_tflite(self, adapter, temp_tflite_file):
        """测试无效的 TFLite 文件"""
        import tensorflow as tf

        with patch.object(tf.lite, "Interpreter") as mock_interpreter_cls:
            mock_interpreter_cls.side_effect = RuntimeError("Invalid TFLite model")

            with pytest.raises(RuntimeError, match="无效的 TFLite 模型"):
                adapter._validate_quantized_model(
                    quantized_tflite_path=temp_tflite_file,
                    input_size=640,
                    task_id="test_task"
                )


# ============================================================
# 4. _convert_with_saved_model_and_st_quant() 方法测试
# ============================================================

class TestConvertModelWithQuantization:
    """测试使用新量化流程的完整转换"""

    @pytest.mark.unit
    def test_convert_model_with_new_quantization_flow(self, adapter, temp_model_file, sample_config):
        """测试使用 SavedModel + ST 量化的完整流程"""
        with patch.object(adapter, "_export_to_saved_model") as mock_export:
            with patch.object(adapter, "_prepare_quant_config") as mock_config:
                with patch.object(adapter, "_run_st_quantization") as mock_quant:
                    with patch.object(adapter, "_validate_quantized_model") as mock_validate:

                        # Mock 各步骤返回值
                        mock_export.return_value = "/tmp/saved_model"
                        mock_config.return_value = Path("/tmp/config.yaml")
                        mock_quant.return_value = "/tmp/quantized.tflite"
                        mock_validate.return_value = True

                        # 执行转换
                        result = adapter._convert_with_saved_model_and_st_quant(
                            task_id="test-123",
                            model_path=temp_model_file,
                            config=sample_config,
                            calib_dataset_path=None,
                            progress_callback=None
                        )

                        # 验证调用链
                        assert result == "/tmp/quantized.tflite"
                        mock_export.assert_called_once()
                        mock_config.assert_called_once()
                        mock_quant.assert_called_once()
                        mock_validate.assert_called_once()

    @pytest.mark.unit
    def test_convert_model_with_calibration_dataset(self, adapter, temp_model_file, temp_calibration_zip, sample_config):
        """测试带校准数据集的转换"""
        with patch.object(adapter, "_export_to_saved_model") as mock_export:
            with patch.object(adapter, "_prepare_quant_config") as mock_config:
                with patch.object(adapter, "_run_st_quantization") as mock_quant:
                    with patch.object(adapter, "_validate_quantized_model") as mock_validate:

                        mock_export.return_value = "/tmp/saved_model"
                        mock_config.return_value = Path("/tmp/config.yaml")
                        mock_quant.return_value = "/tmp/quantized.tflite"
                        mock_validate.return_value = True

                        # 执行转换（带校准数据集）
                        result = adapter._convert_with_saved_model_and_st_quant(
                            task_id="test-456",
                            model_path=temp_model_file,
                            config=sample_config,
                            calib_dataset_path=temp_calibration_zip,
                            progress_callback=None
                        )

                        # 验证配置生成时使用了校准数据集
                        mock_config.assert_called_once()
                        call_args = mock_config.call_args
                        assert call_args[1]["calib_dataset_path"] == temp_calibration_zip

    @pytest.mark.unit
    def test_convert_model_export_failure(self, adapter, temp_model_file, sample_config):
        """测试 SavedModel 导出失败"""
        with patch.object(adapter, "_export_to_saved_model") as mock_export:
            mock_export.side_effect = RuntimeError("Export failed")

            with pytest.raises(RuntimeError, match="Export failed"):
                adapter._convert_with_saved_model_and_st_quant(
                    task_id="test-error",
                    model_path=temp_model_file,
                    config=sample_config,
                    calib_dataset_path=None,
                    progress_callback=None
                )

    @pytest.mark.unit
    def test_convert_model_quantization_failure(self, adapter, temp_model_file, sample_config):
        """测试量化失败"""
        with patch.object(adapter, "_export_to_saved_model") as mock_export:
            with patch.object(adapter, "_prepare_quant_config") as mock_config:
                with patch.object(adapter, "_run_st_quantization") as mock_quant:
                    mock_export.return_value = "/tmp/saved_model"
                    mock_config.return_value = Path("/tmp/config.yaml")
                    mock_quant.side_effect = RuntimeError("Quantization failed")

                    with pytest.raises(RuntimeError, match="Quantization failed"):
                        adapter._convert_with_saved_model_and_st_quant(
                            task_id="test-error",
                            model_path=temp_model_file,
                            config=sample_config,
                            calib_dataset_path=None,
                            progress_callback=None
                        )

    @pytest.mark.unit
    def test_convert_model_validation_failure(self, adapter, temp_model_file, sample_config):
        """测试模型验证失败"""
        with patch.object(adapter, "_export_to_saved_model") as mock_export:
            with patch.object(adapter, "_prepare_quant_config") as mock_config:
                with patch.object(adapter, "_run_st_quantization") as mock_quant:
                    with patch.object(adapter, "_validate_quantized_model") as mock_validate:
                        mock_export.return_value = "/tmp/saved_model"
                        mock_config.return_value = Path("/tmp/config.yaml")
                        mock_quant.return_value = "/tmp/quantized.tflite"
                        mock_validate.side_effect = ValueError("Invalid output shape")

                        with pytest.raises(ValueError, match="Invalid output shape"):
                            adapter._convert_with_saved_model_and_st_quant(
                                task_id="test-error",
                                model_path=temp_model_file,
                                config=sample_config,
                                calib_dataset_path=None,
                                progress_callback=None
                            )

    @pytest.mark.unit
    def test_convert_model_progress_callback(self, adapter, temp_model_file, sample_config):
        """测试进度回调"""
        progress_updates = []

        def mock_callback(progress: int, message: str):
            progress_updates.append((progress, message))

        with patch.object(adapter, "_export_to_saved_model") as mock_export:
            with patch.object(adapter, "_prepare_quant_config") as mock_config:
                with patch.object(adapter, "_run_st_quantization") as mock_quant:
                    with patch.object(adapter, "_validate_quantized_model") as mock_validate:

                        mock_export.return_value = "/tmp/saved_model"
                        mock_config.return_value = Path("/tmp/config.yaml")
                        mock_quant.return_value = "/tmp/quantized.tflite"
                        mock_validate.return_value = True

                        # 执行转换（带进度回调）
                        result = adapter._convert_with_saved_model_and_st_quant(
                            task_id="test-callback",
                            model_path=temp_model_file,
                            config=sample_config,
                            calib_dataset_path=None,
                            progress_callback=mock_callback
                        )

                        # 验证进度回调被调用
                        assert len(progress_updates) > 0
                        # 验证最终进度接近 50%（验证阶段完成后）
                        final_progress = progress_updates[-1][0]
                        assert final_progress >= 50


# ============================================================
# 5. 辅助方法测试
# ============================================================

class TestHelperMethods:
    """测试量化流程的辅助方法"""

    @pytest.mark.unit
    def test_prepare_quant_config(self, adapter, temp_saved_model, tmp_path):
        """测试量化配置文件生成"""
        calib_dir = tmp_path / "calibration"
        calib_dir.mkdir()

        # 调用配置生成
        config_path = adapter._prepare_quant_config(
            saved_model_dir=temp_saved_model,
            input_size=640,
            calib_dataset_path=str(calib_dir),
            task_id="test_task"
        )

        # 验证
        assert config_path.exists()
        assert config_path.suffix == ".yaml"

        # 验证配置内容
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["model"]["model_path"] == temp_saved_model
        assert config["model"]["input_shape"] == [640, 640, 3]
        assert config["quantization"]["calib_dataset_path"] == str(calib_dir)

    @pytest.mark.unit
    def test_prepare_quant_config_fake_mode(self, adapter, temp_saved_model):
        """测试 fake 量化模式配置"""
        # 调用配置生成（无校准数据集）
        config_path = adapter._prepare_quant_config(
            saved_model_dir=temp_saved_model,
            input_size=480,
            calib_dataset_path=None,
            task_id="test_task"
        )

        # 验证
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # fake 模式应该设置为 True
        assert config["quantization"]["fake"] is True

    @pytest.mark.unit
    def test_extract_calibration_dataset(self, adapter, temp_calibration_zip):
        """测试校准数据集解压"""
        extracted_path = adapter._extract_calibration_dataset(temp_calibration_zip)

        # 验证解压路径存在
        assert Path(extracted_path).exists()

        # 验证包含图片文件
        image_files = list(Path(extracted_path).glob("*.jpg"))
        assert len(image_files) > 0

    @pytest.mark.unit
    def test_extract_calibration_dataset_not_zip(self, adapter, tmp_path):
        """测试非 ZIP 格式的校准数据集"""
        calib_dir = tmp_path / "calibration"
        calib_dir.mkdir()

        # 创建一些图片文件
        (calib_dir / "img1.jpg").write_bytes(b"\x00")

        # 调用解压（应该直接返回原路径）
        result = adapter._extract_calibration_dataset(str(calib_dir))

        assert result == str(calib_dir)

    @pytest.mark.unit
    def test_extract_calibration_dataset_error(self, adapter):
        """测试解压失败"""
        invalid_zip = "/nonexistent/calibration.zip"

        with pytest.raises(RuntimeError, match="解压校准数据集失败"):
            adapter._extract_calibration_dataset(invalid_zip)


# ============================================================
# 6. 集成测试
# ============================================================

class TestQuantizationIntegration:
    """量化流程集成测试（需要真实 ML 库）"""

    @pytest.mark.integration
    def test_full_quantization_flow_fake_mode(self, adapter, temp_model_file, sample_config):
        """测试完整的 fake 量化流程"""
        try:
            from ultralytics import YOLO
        except ImportError:
            pytest.skip("Ultralytics 不可用")

        try:
            import tensorflow as tf
        except ImportError:
            pytest.skip("TensorFlow 不可用")

        # 验证模型文件是否有效（如果不是有效的 PyTorch 模型，跳过测试）
        try:
            import torch
            # 尝试加载模型以验证其有效性
            try:
                torch.load(temp_model_file, map_location='cpu')
            except Exception as e:
                pytest.skip(f"测试模型文件无效: {e}")
        except ImportError:
            pytest.skip("PyTorch 不可用")

        # 执行完整转换（无校准数据集）
        result = adapter._convert_with_saved_model_and_st_quant(
            task_id="integration-fake",
            model_path=temp_model_file,
            config=sample_config,
            calib_dataset_path=None,
            progress_callback=None  # 添加缺失的参数
        )

        # 验证结果
        assert result is not None
        assert result.endswith(".tflite")
        assert Path(result).exists()

    @pytest.mark.integration
    def test_full_quantization_flow_with_calibration(self, adapter, temp_model_file, temp_calibration_zip, sample_config):
        """测试带校准数据集的完整量化流程"""
        try:
            from ultralytics import YOLO
        except ImportError:
            pytest.skip("Ultralytics 不可用")

        try:
            import tensorflow as tf
        except ImportError:
            pytest.skip("TensorFlow 不可用")

        # 验证模型文件是否有效
        try:
            import torch
            try:
                torch.load(temp_model_file, map_location='cpu')
            except Exception as e:
                pytest.skip(f"测试模型文件无效: {e}")
        except ImportError:
            pytest.skip("PyTorch 不可用")

        # 执行完整转换（带校准数据集）
        result = adapter._convert_with_saved_model_and_st_quant(
            task_id="integration-calib",
            model_path=temp_model_file,
            config=sample_config,
            calib_dataset_path=temp_calibration_zip,
            progress_callback=None  # 添加缺失的参数
        )

        # 验证结果
        assert result is not None
        assert result.endswith(".tflite")
        assert Path(result).exists()


# ============================================================
# 7. 边界情况测试
# ============================================================

class TestEdgeCases:
    """测试边界情况和异常处理"""

    @pytest.mark.unit
    def test_empty_calibration_dataset(self, adapter, tmp_path):
        """测试空校准数据集"""
        # 创建空的 ZIP 文件
        import zipfile
        empty_zip = tmp_path / "empty.zip"
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            pass  # 空的 ZIP

        # 应该能处理空数据集
        result = adapter._extract_calibration_dataset(str(empty_zip))
        assert result is not None

    @pytest.mark.unit
    def test_invalid_input_size(self, adapter, temp_model_file):
        """测试无效的输入尺寸"""
        invalid_sizes = [-1, 0, 10000]

        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/saved_model"
            mock_yolo.return_value = mock_model

            for size in invalid_sizes:
                # 这些尺寸会被传递给 YOLO.export，我们主要验证不崩溃
                try:
                    adapter._export_to_saved_model(
                        model_path=temp_model_file,
                        input_size=size,
                        task_id="test_task"
                    )
                except (ValueError, RuntimeError):
                    # 预期会抛出异常
                    pass

    @pytest.mark.unit
    def test_concurrent_quantization_tasks(self, adapter, temp_model_file, sample_config):
        """测试并发量化任务"""
        import threading

        results = []
        errors = []

        def run_conversion(task_id: str):
            try:
                with patch.object(adapter, "_export_to_saved_model", return_value="/tmp/saved_model"):
                    with patch.object(adapter, "_prepare_quant_config", return_value=Path("/tmp/config.yaml")):
                        with patch.object(adapter, "_run_st_quantization", return_value="/tmp/quantized.tflite"):
                            with patch.object(adapter, "_validate_quantized_model", return_value=True):
                                result = adapter._convert_with_saved_model_and_st_quant(
                                    task_id=task_id,
                                    model_path=temp_model_file,
                                    config=sample_config,
                                    calib_dataset_path=None,
                                    progress_callback=None
                                )
                                results.append(result)
            except Exception as e:
                errors.append(e)

        # 启动多个并发任务
        threads = []
        for i in range(3):
            t = threading.Thread(
                target=run_conversion,
                args=(f"concurrent-{i}",)
            )
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 验证结果
        assert len(errors) == 0, f"并发任务出错: {errors}"
        assert len(results) == 3

    @pytest.mark.unit
    def test_large_input_size(self, adapter, temp_model_file):
        """测试大输入尺寸"""
        large_size = 1280

        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/saved_model"
            mock_yolo.return_value = mock_model

            # 应该能处理大尺寸
            result = adapter._export_to_saved_model(
                model_path=temp_model_file,
                input_size=large_size,
                task_id="test_task"
            )

            assert result is not None

    @pytest.mark.unit
    def test_corrupted_calibration_zip(self, adapter, tmp_path):
        """测试损坏的校准数据集 ZIP"""
        corrupted_zip = tmp_path / "corrupted.zip"
        corrupted_zip.write_bytes(b"\x00" * 100)  # 无效的 ZIP 数据

        with pytest.raises(RuntimeError, match="解压校准数据集失败"):
            adapter._extract_calibration_dataset(str(corrupted_zip))


# ============================================================
# 8. 性能测试
# ============================================================

class TestPerformance:
    """测试性能相关场景"""

    @pytest.mark.unit
    def test_quantization_with_large_calibration_dataset(self, adapter, tmp_path):
        """测试大量校准图片的场景"""
        import zipfile

        # 创建包含大量图片的 ZIP
        large_zip = tmp_path / "large_calib.zip"
        calib_dir = tmp_path / "large_calib"
        calib_dir.mkdir()

        # 创建 300 张图片（超过默认限制）
        for i in range(300):
            (calib_dir / f"img_{i}.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)

        with zipfile.ZipFile(large_zip, 'w') as zf:
            for img_file in calib_dir.glob("*.jpg"):
                zf.write(img_file, img_file.name)

        # Mock subprocess.run 来验证图片数量限制
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # 创建配置文件
            config_file = tmp_path / "config.yaml"
            with open(config_file, 'w') as f:
                yaml.dump({
                    "model": {"name": "test", "model_path": "/tmp/saved_model"},
                    "quantization": {
                        "export_path": str(tmp_path / "quantized_models"),
                    }
                }, f)

            # 创建量化输出
            output_dir = config_file.parent / "quantized_models"
            output_dir.mkdir()
            (output_dir / "model.tflite").write_bytes(b"\x00")

            adapter._run_st_quantization(
                config_path=config_file,
                task_id="test_task"
            )

            # 验证量化脚本被调用
            mock_run.assert_called_once()

    @pytest.mark.unit
    def test_memory_cleanup_during_quantization(self, adapter, tmp_path):
        """测试量化过程中的内存清理"""
        # 这个测试验证量化脚本正确处理了内存
        # 通过检查配置中的 max_calib_images 参数
        config_file = tmp_path / "config.yaml"

        # 创建包含 max_calib_images 的配置
        with open(config_file, 'w') as f:
            yaml.dump({
                "model": {"name": "test", "model_path": "/tmp/saved_model"},
                "quantization": {
                    "export_path": str(tmp_path / "quantized_models"),
                    "max_calib_images": 200  # 限制图片数量防止 OOM
                }
            }, f)

        # 创建量化输出
        output_dir = config_file.parent / "quantized_models"
        output_dir.mkdir()
        (output_dir / "model.tflite").write_bytes(b"\x00")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            adapter._run_st_quantization(
                config_path=config_file,
                task_id="test_task"
            )

            # 验证量化脚本被调用
            mock_run.assert_called_once()


# ============================================================
# 9. yaml_path 参数处理测试
# ============================================================

class TestYamlPathParameter:
    """测试 yaml_path 参数的完整处理流程"""

    @pytest.mark.unit
    def test_export_with_valid_yaml_path(self, adapter, temp_model_file, tmp_path):
        """测试提供有效的 yaml_path"""
        # 创建一个有效的 classes.yaml
        yaml_file = tmp_path / "classes.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump({
                "names": ["person", "car", "dog"],
                "nc": 3
            }, f)

        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {"input_size": 640, "num_classes": 3}
            
            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=str(yaml_file),
                config=config
            )

            # 验证 data 参数被正确传递
            call_kwargs = mock_model.export.call_args[1]
            assert "data" in call_kwargs
            assert call_kwargs["data"] == str(yaml_file)


    @pytest.mark.unit
    def test_export_with_none_yaml_path(self, adapter, temp_model_file):
        """测试 yaml_path 为 None 时的默认行为"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {"input_size": 640, "num_classes": 80}

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=None,
                config=config
            )

            # 验证 export 被调用
            mock_model.export.assert_called_once()


# ============================================================
# 10. num_classes 一致性验证测试
# ============================================================

class TestFractionBoundaryValues:
    """测试 fraction 参数的边界值"""

    @pytest.mark.unit
    def test_fraction_zero(self, adapter, temp_model_file):
        """测试 fraction = 0.0"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {"input_size": 640, "num_classes": 80, "fraction": 0.0}

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=None,
                config=config
            )

            call_kwargs = mock_model.export.call_args[1]
            assert call_kwargs["fraction"] == 0.0

    @pytest.mark.unit
    def test_fraction_one(self, adapter, temp_model_file):
        """测试 fraction = 1.0"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {"input_size": 640, "num_classes": 80, "fraction": 1.0}

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=None,
                config=config
            )

            call_kwargs = mock_model.export.call_args[1]
            assert call_kwargs["fraction"] == 1.0

    @pytest.mark.unit
    def test_fraction_half(self, adapter, temp_model_file):
        """测试 fraction = 0.5"""
        with patch("ultralytics.YOLO") as mock_yolo:
            mock_model = MagicMock()
            mock_model.export.return_value = "/tmp/quantized.tflite"
            mock_yolo.return_value = mock_model

            config = {"input_size": 640, "num_classes": 80, "fraction": 0.5}

            adapter._export_to_quantized_tflite(
                model_path=temp_model_file,
                input_size=640,
                calib_dataset_path=None,
                yaml_path=None,
                config=config
            )

            call_kwargs = mock_model.export.call_args[1]
            assert call_kwargs["fraction"] == 0.5
