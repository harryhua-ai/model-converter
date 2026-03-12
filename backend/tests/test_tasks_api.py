"""
测试任务 API
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.task_manager import get_task_manager
from app.models.schemas import ConversionConfig


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_task():
    """创建示例任务"""
    task_manager = get_task_manager()
    config = ConversionConfig()
    task_id = task_manager.create_task(config)
    return task_id


def test_get_task_status_success(client, sample_task):
    """测试成功获取任务状态"""
    response = client.get(f"/api/tasks/{sample_task}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["task_id"] == sample_task
    assert "status" in data
    assert "progress" in data
    assert "current_step" in data
    assert "config" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_get_task_status_not_found(client):
    """测试获取不存在的任务"""
    response = client.get("/api/tasks/nonexistent-task-id")
    
    assert response.status_code == 404
    assert "任务不存在" in response.json()["detail"]


def test_list_tasks_empty(client):
    """测试列出任务(空列表)"""
    # 注意: 这可能受到其他测试影响,所以只验证响应结构
    response = client.get("/api/tasks")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_tasks_with_data(client, sample_task):
    """测试列出任务(有数据)"""
    response = client.get("/api/tasks")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # 验证至少有一个任务
    assert len(data) >= 1
    
    # 验证任务结构
    task = data[0]
    assert "task_id" in task
    assert "status" in task
    assert "progress" in task


def test_task_status_values(client, sample_task):
    """测试任务状态字段的有效性"""
    response = client.get(f"/api/tasks/{sample_task}")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证状态值
    assert data["status"] in ["pending", "running", "completed", "failed"]
    
    # 验证进度范围
    assert 0 <= data["progress"] <= 100
    
    # 验证配置
    assert "model_type" in data["config"]
    assert "input_size" in data["config"]
    assert "num_classes" in data["config"]


def test_list_multiple_tasks(client):
    """测试列出多个任务"""
    task_manager = get_task_manager()
    config = ConversionConfig()
    
    # 创建多个任务
    task_ids = []
    for _ in range(3):
        task_id = task_manager.create_task(config)
        task_ids.append(task_id)
    
    response = client.get("/api/tasks")
    
    assert response.status_code == 200
    data = response.json()
    
    # 验证至少有 3 个任务
    assert len(data) >= 3
    
    # 验证创建的任务都在列表中
    response_task_ids = [task["task_id"] for task in data]
    for task_id in task_ids:
        assert task_id in response_task_ids
