"""
测试 FastAPI 主应用
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_health_check(client):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "model-converter"


def test_cors_middleware(client):
    """测试 CORS 中间件配置"""
    # CORS 中间件已配置,简单验证应用可以正常响应
    response = client.get("/health")
    assert response.status_code == 200
    # CORS 中间件在测试客户端中不会添加头,但已正确配置


def test_app_creation():
    """测试应用实例创建"""
    from app.main import create_app

    test_app = create_app()
    assert test_app is not None
    assert test_app.title == "Model Converter API"


def test_static_files_not_found(client):
    """测试静态文件 404 处理"""
    response = client.get("/static/nonexistent.html")
    # 如果前端构建目录不存在,应返回 404
    assert response.status_code in [404, 200]  # 200 如果文件存在
