"""
真实转换流程的集成测试

注意: 这些测试需要:
1. 真实的模型文件 (tests/fixtures/yolov8n.pt)
2. Docker 环境运行
3. 完整的工具链依赖

默认情况下会跳过,除非明确标记为运行集成测试
"""

import io
import json
import pytest
import time
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_model_file():
    """示例模型文件路径"""
    model_path = Path("tests/fixtures/yolov8n.pt")
    return model_path


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


@pytest.mark.integration
@pytest.mark.slow
def test_full_conversion_workflow(client, sample_model_file, sample_config):
    """
    测试完整的转换流程（需要 Docker）

    此测试会:
    1. 上传模型文件和配置
    2. 启动转换任务
    3. 轮询任务状态直到完成
    4. 验证输出文件

    预计耗时: 5-10 分钟
    """
    # 检查模型文件是否存在
    if not sample_model_file.exists():
        pytest.skip(f"需要真实的测试模型文件: {sample_model_file}")

    # 准备测试文件
    model_content = sample_model_file.read_bytes()

    # 上传并启动转换
    response = client.post(
        "/api/convert",
        files={
            "model_file": (sample_model_file.name, model_content, "application/octet-stream"),
            "config_file": ("config.json", json.dumps(sample_config), "application/json")
        }
    )

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"

    # 轮询任务状态
    task_id = data["task_id"]
    max_attempts = 60  # 最多等待 5 分钟 (60 * 5秒)
    attempt = 0

    while attempt < max_attempts:
        time.sleep(5)  # 等待 5 秒

        status_response = client.get(f"/api/tasks/{task_id}")
        status_data = status_response.json()

        # 检查状态
        if status_data["status"] == "completed":
            # 验证输出文件存在
            output_filename = status_data.get("output_filename")
            assert output_filename is not None
            print(f"\n✅ 转换成功完成: {output_filename}")
            break
        elif status_data["status"] == "failed":
            error_msg = status_data.get("error_message", "未知错误")
            pytest.fail(f"转换失败: {error_msg}")
        elif status_data["status"] == "processing":
            # 打印进度信息
            progress = status_data.get("progress", 0)
            step = status_data.get("current_step", "")
            print(f"\n进度: {progress}% - {step}")

        attempt += 1

    # 最终验证
    assert status_data["status"] == "completed", f"任务在 {max_attempts * 5} 秒内未完成"
    assert status_data["progress"] == 100
    assert status_data.get("output_filename") is not None


@pytest.mark.integration
@pytest.mark.slow
def test_conversion_with_calibration(client, sample_model_file):
    """
    测试带校准数据集的转换流程

    此测试需要额外的校准数据集
    """
    if not sample_model_file.exists():
        pytest.skip(f"需要真实的测试模型文件: {sample_model_file}")

    # 检查校准数据集
    calib_dataset = Path("tests/fixtures/calibration_images")
    if not calib_dataset.exists():
        pytest.skip(f"需要校准数据集: {calib_dataset}")

    config_with_calib = {
        "model_type": "YOLOv8",
        "input_size": 480,
        "num_classes": 80,
        "confidence_threshold": 0.25,
        "quantization": "int8",
        "use_calibration": True,
        "calib_dataset_path": str(calib_dataset)
    }

    model_content = sample_model_file.read_bytes()

    response = client.post(
        "/api/convert",
        files={
            "model_file": (sample_model_file.name, model_content, "application/octet-stream"),
            "config_file": ("config.json", json.dumps(config_with_calib), "application/json")
        }
    )

    assert response.status_code == 202
    data = response.json()
    task_id = data["task_id"]

    # 轮询任务状态
    for _ in range(60):
        time.sleep(5)
        status_response = client.get(f"/api/tasks/{task_id}")
        status_data = status_response.json()

        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"转换失败: {status_data.get('error_message')}")

    assert status_data["status"] == "completed"


@pytest.mark.integration
def test_conversion_error_handling(client, sample_config):
    """
    测试转换过程中的错误处理

    使用无效的模型文件来测试错误处理
    """
    # 创建一个无效的"模型文件"
    invalid_model = io.BytesIO(b"this is not a valid model file")
    invalid_model.name = "invalid.pt"

    response = client.post(
        "/api/convert",
        files={
            "model_file": ("invalid.pt", invalid_model, "application/octet-stream"),
            "config_file": ("config.json", json.dumps(sample_config), "application/json")
        }
    )

    # 任务应该被创建,但后续会失败
    assert response.status_code == 202
    task_id = response.json()["task_id"]

    # 等待任务失败
    time.sleep(10)

    status_response = client.get(f"/api/tasks/{task_id}")
    status_data = status_response.json()

    # 验证任务失败且有错误信息
    assert status_data["status"] in ["failed", "processing"]
    if status_data["status"] == "failed":
        assert status_data.get("error_message") is not None
