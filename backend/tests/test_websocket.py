"""
测试 WebSocket 端点
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from app.api.websocket import ConnectionManager


def test_connection_manager_init():
    """测试连接管理器初始化"""
    manager = ConnectionManager()
    assert manager.active_connections == {}
    assert isinstance(manager.active_connections, dict)


def test_connection_manager_connect():
    """测试连接管理器的连接功能"""
    import asyncio
    
    manager = ConnectionManager()
    
    # 创建 mock WebSocket
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    
    async def test_connect():
        await manager.connect(websocket, "test-task-1")
        assert "test-task-1" in manager.active_connections
        assert websocket in manager.active_connections["test-task-1"]
        # 验证 accept 被调用
        websocket.accept.assert_called_once()
    
    asyncio.run(test_connect())


def test_connection_manager_disconnect():
    """测试连接管理器的断开功能"""
    import asyncio
    
    manager = ConnectionManager()
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    
    async def test():
        # 先连接
        await manager.connect(websocket, "test-task-1")
        assert websocket in manager.active_connections["test-task-1"]
        
        # 再断开
        manager.disconnect(websocket, "test-task-1")
        assert websocket not in manager.active_connections.get("test-task-1", set())
    
    asyncio.run(test())


def test_connection_manager_broadcast():
    """测试广播功能"""
    import asyncio
    
    manager = ConnectionManager()
    
    # 创建多个 mock WebSocket
    websocket1 = MagicMock()
    websocket1.accept = AsyncMock()
    websocket1.send_json = AsyncMock()
    
    websocket2 = MagicMock()
    websocket2.accept = AsyncMock()
    websocket2.send_json = AsyncMock()
    
    async def test():
        # 连接多个 WebSocket
        await manager.connect(websocket1, "test-task-1")
        await manager.connect(websocket2, "test-task-1")
        
        # 广播消息
        message = {"type": "progress", "data": 50}
        await manager.broadcast_to_task("test-task-1", message)
        
        # 验证两个 WebSocket 都收到消息
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
    
    asyncio.run(test())


def test_connection_manager_cleanup_empty_tasks():
    """测试清理空任务"""
    import asyncio
    
    manager = ConnectionManager()
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    
    async def test():
        # 连接
        await manager.connect(websocket, "test-task-1")
        assert "test-task-1" in manager.active_connections
        
        # 断开 - 应该清理空任务
        manager.disconnect(websocket, "test-task-1")
        assert "test-task-1" not in manager.active_connections
    
    asyncio.run(test())


def test_connection_manager_send_personal_message():
    """测试发送个人消息"""
    import asyncio
    
    manager = ConnectionManager()
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    
    async def test():
        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(message, websocket)
        
        websocket.send_json.assert_called_once_with(message)
    
    asyncio.run(test())
