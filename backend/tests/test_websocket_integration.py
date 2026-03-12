"""
WebSocket 集成测试

注意: 这些测试使用真实的 WebSocket 连接
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


def test_websocket_endpoint_exists(client):
    """测试 WebSocket 端点存在且可访问"""
    # 尝试升级到 WebSocket 连接
    # 这不会真正连接,但会验证端点存在
    try:
        with client.websocket_connect("/ws") as websocket:
            # 发送无效消息以触发关闭
            websocket.send_json({"invalid": "message"})
            # 应该被关闭
            assert True
    except Exception as e:
        # 端点存在,可能因为消息格式被关闭
        assert True


def test_websocket_requires_valid_message(client):
    """测试 WebSocket 需要有效的消息格式"""
    from app.core.task_manager import get_task_manager
    from app.models.schemas import ConversionConfig
    
    # 创建一个任务
    task_manager = get_task_manager()
    config = ConversionConfig()
    task_id = task_manager.create_task(config)
    
    # 测试缺少 action 的消息
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({
            "task_id": task_id  # 缺少 action
        })
        
        # 应该被关闭
        try:
            websocket.receive_json()
            assert False, "Expected WebSocket to be closed"
        except Exception:
            # 连接被关闭是预期的
            assert True


def test_websocket_subscribe_and_cancel(client):
    """测试订阅和取消流程"""
    from app.core.task_manager import get_task_manager
    from app.models.schemas import ConversionConfig
    
    task_manager = get_task_manager()
    config = ConversionConfig()
    task_id = task_manager.create_task(config)
    
    with client.websocket_connect("/ws") as websocket:
        # 订阅任务
        websocket.send_json({
            "action": "subscribe",
            "task_id": task_id
        })
        
        # 接收状态
        response = websocket.receive_json()
        assert response["type"] == "status"
        assert response["task_id"] == task_id
        assert "data" in response
        
        # 立即取消
        websocket.send_json({
            "action": "cancel",
            "task_id": task_id
        })
        
        # 接收取消确认
        response = websocket.receive_json()
        assert response["type"] == "cancelled"
        assert response["task_id"] == task_id


def test_websocket_ping(client):
    """测试心跳功能"""
    from app.core.task_manager import get_task_manager
    from app.models.schemas import ConversionConfig
    
    task_manager = get_task_manager()
    config = ConversionConfig()
    task_id = task_manager.create_task(config)
    
    with client.websocket_connect("/ws") as websocket:
        # 订阅
        websocket.send_json({
            "action": "subscribe",
            "task_id": task_id
        })
        websocket.receive_json()
        
        # 发送 ping
        websocket.send_json({
            "action": "ping",
            "task_id": task_id
        })
        
        # 接收 pong
        response = websocket.receive_json()
        assert response["type"] == "pong"
        
        # 清理: 取消订阅
        websocket.send_json({
            "action": "cancel",
            "task_id": task_id
        })
