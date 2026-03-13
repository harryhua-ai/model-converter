"""
API 端点测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestPresetsAPI:
    """配置预设 API 测试"""

    def test_get_presets(self, client: TestClient):
        """测试获取配置预设列表"""
        response = client.get("/api/v1/presets")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # 验证预设结构
        preset = data[0]
        assert "id" in preset
        assert "name" in preset
        assert "description" in preset
        assert "config" in preset

    def test_get_preset_by_id(self, client: TestClient):
        """测试获取指定配置预设"""
        response = client.get("/api/v1/presets/yolov8n-480")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "yolov8n-480"
        assert "YOLOv8n 480x480" in data["name"]


class TestTasksAPI:
    """任务管理 API 测试"""

    def test_get_tasks_empty(self, client: TestClient):
        """测试获取空任务列表"""
        response = client.get("/api/v1/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert isinstance(data["tasks"], list)

    def test_get_task_not_found(self, client: TestClient):
        """测试获取不存在的任务"""
        response = client.get("/api/v1/tasks/non-existent-id")

        assert response.status_code == 404


class TestHealthCheck:
    """健康检查测试"""

    def test_health_check(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data

    def test_root_endpoint(self, client: TestClient):
        """测试根路径端点"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestModelValidation:
    """模型验证测试"""

    def test_invalid_file_extension(self, client: TestClient, sample_config):
        """测试不支持的文件格式"""
        # 创建假的 .txt 文件
        import tempfile
        import io

        files = {
            'file': ('model.txt', io.BytesIO(b'invalid data'), 'text/plain'),
            'config': (None, str(sample_config), 'application/json')
        }

        response = client.post("/api/v1/models/upload", files=files)

        # 应该返回错误
        assert response.status_code in [400, 422]

    def test_missing_file(self, client: TestClient, sample_config):
        """测试缺少文件"""
        response = client.post(
            "/api/v1/models/upload",
            data={"config": str(sample_config)}
        )

        # 应该返回错误
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
