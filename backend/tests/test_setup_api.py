"""
测试设置 API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_check_setup_success(client):
    """测试成功检查环境设置"""
    response = client.get("/api/setup/check")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证响应结构
    assert "status" in data
    assert "mode" in data
    assert "message" in data
    
    # 验证状态值
    assert data["status"] in ["ready", "docker_not_installed", "image_pull_required", "not_configured"]
    assert data["mode"] in ["docker", "none"]


@patch("app.api.setup.EnvironmentDetector")
def test_check_setup_exception_handling(mock_detector_class, client):
    """测试异常处理"""
    # 模拟异常
    mock_detector_class.side_effect = Exception("检测失败")
    
    response = client.get("/api/setup/check")
    
    # 应该返回 200 和错误状态
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_configured"
    assert "检测失败" in data["message"] or "error" in data


def test_check_setup_response_structure(client):
    """测试响应结构的完整性"""
    response = client.get("/api/setup/check")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证所有必需字段
    required_fields = ["status", "mode", "message"]
    for field in required_fields:
        assert field in data, f"缺少必需字段: {field}"
    
    # 验证可选字段存在时的有效性
    if "guide" in data and data["guide"] is not None:
        assert isinstance(data["guide"], dict)


def test_check_setup_logs(client, caplog):
    """测试环境检查日志记录"""
    with caplog.at_level("INFO"):
        response = client.get("/api/setup/check")
    
    assert response.status_code == 200
    # 验证日志被记录
    assert any("环境检查" in record.message for record in caplog.records)
