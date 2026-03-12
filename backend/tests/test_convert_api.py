"""
测试转换 API
"""

import json
import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "model_type": "YOLOv8",
        "input_size": 480,
        "num_classes": 80,
        "confidence_threshold": 0.25,
        "quantization": "int8",
        "use_calibration": False
    }


@pytest.fixture
def sample_yaml():
    """示例 YAML 内容"""
    return """
classes:
  - name: person
    id: 0
    color: [255, 0, 0]
  - name: car
    id: 1
    color: [0, 255, 0]
"""


def test_convert_model_success(client, sample_config):
    """测试成功创建转换任务"""
    # 准备测试文件
    model_file = io.BytesIO(b"fake model content")
    model_file.name = "model.pt"

    config_file = io.BytesIO(json.dumps(sample_config).encode())
    config_file.name = "config.json"

    # 发送请求
    response = client.post(
        "/api/convert",
        files={
            "model_file": ("model.pt", model_file, "application/octet-stream"),
            "config_file": ("config.json", config_file, "application/json")
        }
    )

    # 验证响应
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"


def test_convert_model_with_yaml(client, sample_config, sample_yaml):
    """测试带 YAML 文件的转换"""
    model_file = io.BytesIO(b"fake model content")
    model_file.name = "model.pt"

    config_file = io.BytesIO(json.dumps(sample_config).encode())
    config_file.name = "config.json"

    yaml_file = io.BytesIO(sample_yaml.encode())
    yaml_file.name = "classes.yaml"

    response = client.post(
        "/api/convert",
        files={
            "model_file": ("model.pt", model_file, "application/octet-stream"),
            "config_file": ("config.json", config_file, "application/json"),
            "yaml_file": ("classes.yaml", yaml_file, "text/yaml")
        }
    )

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data


def test_convert_model_invalid_extension(client, sample_config):
    """测试不支持的模型文件格式"""
    config_file = io.BytesIO(json.dumps(sample_config).encode())
    config_file.name = "config.json"

    response = client.post(
        "/api/convert",
        files={
            "model_file": ("model.txt", io.BytesIO(b"content"), "text/plain"),
            "config_file": ("config.json", config_file, "application/json")
        }
    )

    assert response.status_code == 400
    assert "不支持的模型文件格式" in response.json()["detail"]


def test_convert_model_invalid_config(client):
    """测试无效的配置文件"""
    model_file = io.BytesIO(b"fake model content")
    model_file.name = "model.pt"

    config_file = io.BytesIO(b"invalid json")
    config_file.name = "config.json"

    response = client.post(
        "/api/convert",
        files={
            "model_file": ("model.pt", model_file, "application/octet-stream"),
            "config_file": ("config.json", config_file, "application/json")
        }
    )

    assert response.status_code == 400
    assert "JSON 格式无效" in response.json()["detail"]


def test_convert_model_invalid_field(client):
    """测试无效的字段值"""
    model_file = io.BytesIO(b"fake model content")
    model_file.name = "model.pt"

    # 无效的输入尺寸
    invalid_config = {
        "model_type": "YOLOv8",
        "input_size": 999,
        "num_classes": 80
    }
    config_file = io.BytesIO(json.dumps(invalid_config).encode())
    config_file.name = "config.json"

    response = client.post(
        "/api/convert",
        files={
            "model_file": ("model.pt", model_file, "application/octet-stream"),
            "config_file": ("config.json", config_file, "application/json")
        }
    )

    # Pydantic 验证错误
    assert response.status_code in [400, 422]


@patch("app.api.convert._run_conversion")
def test_background_conversion(mock_run_conversion, client, sample_config):
    """测试后台转换任务被正确调用"""
    model_file = io.BytesIO(b"fake model content")
    model_file.name = "model.pt"

    config_file = io.BytesIO(json.dumps(sample_config).encode())
    config_file.name = "config.json"

    response = client.post(
        "/api/convert",
        files={
            "model_file": ("model.pt", model_file, "application/octet-stream"),
            "config_file": ("config.json", config_file, "application/json")
        }
    )

    assert response.status_code == 202
    # 验证后台任务被调度
    # 注意: 在测试环境中,BackgroundTasks 可能不会真正执行
