"""
NE301 配置生成工具测试

测试 ne301_config.py 模块的核心功能
"""
import pytest
from pathlib import Path
from app.core.ne301_config import (
    calculate_total_boxes,
    calculate_memory_pools,
    generate_ne301_json_config,
    _convert_to_json_serializable
)


class TestCalculateTotalBoxes:
    """测试 total_boxes 计算"""

    def test_standard_input_sizes(self):
        """测试标准输入尺寸的 total_boxes 计算"""
        assert calculate_total_boxes(256) == 1344
        assert calculate_total_boxes(320) == 2100
        assert calculate_total_boxes(416) == 3549
        assert calculate_total_boxes(480) == 4725
        assert calculate_total_boxes(640) == 8400

    def test_custom_input_size(self):
        """测试自定义输入尺寸（使用通用公式）"""
        # 测试 512 (通用公式)
        total_boxes = calculate_total_boxes(512)
        assert isinstance(total_boxes, int)
        assert total_boxes > 0

        # 验证通用公式的正确性
        # scale = 512 // 8 = 64
        # total_boxes = 3 * (64^2 + 32^2 + 16^2) = 3 * (4096 + 1024 + 256) = 3 * 5376 = 16128
        assert total_boxes == 16128


class TestCalculateMemoryPools:
    """测试内存池计算"""

    def test_minimum_memory_pools(self):
        """测试最小内存池限制"""
        # 小模型（1MB）
        model_size = 1 * 1024 * 1024
        exec_pool, ext_pool = calculate_memory_pools(model_size, 640, 8400)

        # 验证最小值
        assert exec_pool >= 1073741824  # >= 1GB
        assert ext_pool >= 2147483648   # >= 2GB

    def test_maximum_memory_pools(self):
        """测试内存池上限"""
        # 大模型（100MB）
        model_size = 100 * 1024 * 1024
        exec_pool, ext_pool = calculate_memory_pools(model_size, 640, 8400)

        # 验证上限
        assert exec_pool <= 2147483648  # <= 2GB
        assert ext_pool <= 4294967296   # <= 4GB

    def test_medium_model(self):
        """测试中等大小模型"""
        # 10MB 模型
        model_size = 10 * 1024 * 1024
        exec_pool, ext_pool = calculate_memory_pools(model_size, 640, 8400)

        # 验证合理性
        assert exec_pool >= 1073741824  # 至少 1GB
        assert ext_pool >= 2147483648   # 至少 2GB
        assert ext_pool > exec_pool     # ext 应该大于 exec

    def test_different_input_sizes(self):
        """测试不同输入尺寸"""
        model_size = 5 * 1024 * 1024

        # 小输入尺寸（256）
        exec_pool_256, ext_pool_256 = calculate_memory_pools(model_size, 256, 1344)

        # 大输入尺寸（640）
        exec_pool_640, ext_pool_640 = calculate_memory_pools(model_size, 640, 8400)

        # 更大的输入尺寸应该需要更多内存
        assert exec_pool_640 >= exec_pool_256
        assert ext_pool_640 >= ext_pool_256


class TestConvertToJsonSerializable:
    """测试 NumPy 类型转换"""

    def test_convert_numpy_int(self):
        """测试 NumPy 整数转换"""
        import numpy as np

        result = _convert_to_json_serializable(np.int32(42))
        assert isinstance(result, int)
        assert result == 42

    def test_convert_numpy_float(self):
        """测试 NumPy 浮点数转换"""
        import numpy as np

        result = _convert_to_json_serializable(np.float32(3.14))
        assert isinstance(result, float)

    def test_convert_numpy_array(self):
        """测试 NumPy 数组转换"""
        import numpy as np

        arr = np.array([1, 2, 3])
        result = _convert_to_json_serializable(arr)
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_convert_dict_with_numpy(self):
        """测试包含 NumPy 类型的字典"""
        import numpy as np

        data = {
            "int": np.int64(100),
            "float": np.float64(3.14),
            "array": np.array([1, 2, 3])
        }

        result = _convert_to_json_serializable(data)

        assert isinstance(result["int"], int)
        assert isinstance(result["float"], float)
        assert isinstance(result["array"], list)

    def test_convert_nested_structure(self):
        """测试嵌套结构转换"""
        import numpy as np

        data = {
            "nested": {
                "values": [np.int32(1), np.int32(2), np.int32(3)],
                "matrix": np.array([[1, 2], [3, 4]])
            }
        }

        result = _convert_to_json_serializable(data)

        assert isinstance(result["nested"]["values"], list)
        assert isinstance(result["nested"]["matrix"], list)


class TestGenerateNe301JsonConfig:
    """测试完整 JSON 配置生成"""

    @pytest.mark.integration
    def test_generate_config_with_real_tflite(self, tmp_path):
        """集成测试：使用真实 TFLite 文件生成配置

        注意：此测试需要真实的 TFLite 模型文件
        如果没有文件，应该跳过
        """
        # 尝试查找现有的 TFLite 文件
        tflite_files = list(Path("/app/outputs").glob("*.tflite"))

        if not tflite_files:
            pytest.skip("没有找到 TFLite 文件，跳过集成测试")

        tflite_path = tflite_files[0]

        config = generate_ne301_json_config(
            tflite_path=tflite_path,
            model_name="test_model",
            input_size=640,
            num_classes=80,
            class_names=["person", "car", "dog"]
        )

        # 验证配置结构
        assert "version" in config
        assert "model_info" in config
        assert "input_spec" in config
        assert "output_spec" in config
        assert "memory" in config
        assert "postprocess_params" in config

        # 验证关键字段
        assert config["model_info"]["input_size"] == 640
        assert config["model_info"]["num_classes"] == 80
        assert config["postprocess_params"]["total_boxes"] == 8400
        assert len(config["postprocess_params"]["class_names"]) == 3

    def test_generate_config_with_defaults(self, tmp_path):
        """测试使用默认值生成配置（不需要真实 TFLite 文件）"""
        # 创建一个临时文件来模拟 TFLite
        fake_tflite = tmp_path / "fake.tflite"
        fake_tflite.write_bytes(b"fake content" * 1000)  # 12KB

        config = generate_ne301_json_config(
            tflite_path=fake_tflite,
            model_name="test_model",
            input_size=640,
            num_classes=30,
            class_names=[f"class_{i}" for i in range(30)]
        )

        # 验证配置完整性
        assert config["version"] == "1.0.0"
        assert config["model_info"]["name"] == "test_model"
        assert config["model_info"]["type"] == "OBJECT_DETECTION"
        assert config["input_spec"]["width"] == 640
        assert config["input_spec"]["height"] == 640
        assert config["input_spec"]["channels"] == 3

        # 验证输出规格
        assert config["output_spec"]["num_outputs"] == 1
        output = config["output_spec"]["outputs"][0]
        assert "scale" in output
        assert "zero_point" in output
        assert output["data_type"] == "int8"

        # 验证内存配置
        assert "exec_memory_pool" in config["memory"]
        assert "ext_memory_pool" in config["memory"]
        assert config["memory"]["alignment_requirement"] == 8

        # 验证后处理参数
        assert config["postprocess_type"] == "pp_od_yolo_v8_ui"
        assert config["postprocess_params"]["num_classes"] == 30
        assert config["postprocess_params"]["total_boxes"] == 8400
        assert len(config["postprocess_params"]["class_names"]) == 30

    def test_config_json_serializable(self, tmp_path):
        """测试配置可以正确序列化为 JSON"""
        import json

        fake_tflite = tmp_path / "fake.tflite"
        fake_tflite.write_bytes(b"fake content" * 1000)

        config = generate_ne301_json_config(
            tflite_path=fake_tflite,
            model_name="test_model",
            input_size=480,
            num_classes=10,
            class_names=[f"class_{i}" for i in range(10)]
        )

        # 验证可以序列化为 JSON
        json_str = json.dumps(config)
        assert isinstance(json_str, str)

        # 验证可以反序列化
        loaded_config = json.loads(json_str)
        assert loaded_config["model_info"]["name"] == "test_model"
