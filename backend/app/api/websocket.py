"""
WebSocket 路由

处理实时进度更新
"""

import json
import logging
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.task_manager import get_task_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # task_id -> WebSocket 连接列表
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """接受连接并订阅任务"""
        # 注意：不要在这里调用 websocket.accept()，因为外层已经调用过了
        # await websocket.accept()  # ❌ 移除这行，避免重复 accept

        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()

        self.active_connections[task_id].add(websocket)

        # ✅ FIX: 同时注册到 TaskManager，使其能够广播进度消息
        task_manager = get_task_manager()
        task_manager.register_websocket(task_id, websocket)

        logger.info(f"WebSocket 连接已建立: task_id={task_id}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        """断开连接"""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)

            # 如果该任务没有连接了,清理字典
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

        # ✅ FIX: 同时从 TaskManager 注销
        task_manager = get_task_manager()
        task_manager.unregister_websocket(task_id, websocket)

        logger.info(f"WebSocket 连接已断开: task_id={task_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送消息给特定连接"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def broadcast_to_task(self, task_id: str, message: dict):
        """向订阅特定任务的所有连接广播消息"""
        if task_id not in self.active_connections:
            return
        
        # 复制连接集合以避免在迭代时修改
        connections = list(self.active_connections[task_id])
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败 (task_id={task_id}): {e}")
                # 移除失败的连接
                self.disconnect(connection, task_id)


# 全局连接管理器实例
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点

    客户端消息格式:
    {
        "action": "subscribe" | "cancel",
        "task_id": "task-uuid"
    }

    服务器推送格式:
    {
        "type": "progress" | "complete" | "error",
        "task_id": "task-uuid",
        "data": {...}
    }
    """
    task_id = None

    try:
        # 第一步：接受 WebSocket 连接（建立握手）
        await websocket.accept()
        logger.info("WebSocket 连接已接受，等待客户端消息...")

        # 第二步：等待客户端发送订阅消息
        logger.info("等待客户端订阅消息...")
        data = await websocket.receive_json()
        logger.info(f"收到客户端消息: {data}")
        action = data.get("action")
        task_id = data.get("task_id")
        logger.info(f"解析消息: action={action}, task_id={task_id}")

        if action == "subscribe" and task_id:
            # 订阅任务进度
            await manager.connect(websocket, task_id)
            
            # 发送当前任务状态
            task_manager = get_task_manager()
            task = task_manager.get_task(task_id)
            
            if task:
                await manager.send_personal_message({
                    "type": "status",
                    "task_id": task_id,
                    "data": {
                        "status": task.status,
                        "progress": task.progress,
                        "current_step": task.current_step,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat()
                    }
                }, websocket)
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "task_id": task_id,
                    "data": {
                        "message": "任务不存在"
                    }
                }, websocket)
        
        elif action == "cancel":
            # 取消订阅
            if task_id:
                await manager.send_personal_message({
                    "type": "cancelled",
                    "task_id": task_id,
                    "data": {"message": "取消订阅"}
                }, websocket)
                await websocket.close()
                return
        else:
            # 无效的消息
            await websocket.close(code=1008, reason="Invalid message format")
            return
        
        # 保持连接并监听后续消息
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "cancel":
                # 取消订阅
                await manager.send_personal_message({
                    "type": "cancelled",
                    "task_id": task_id,
                    "data": {"message": "取消订阅"}
                }, websocket)
                break
            elif action == "ping":
                # 心跳检测
                await manager.send_personal_message({
                    "type": "pong",
                    "task_id": task_id
                }, websocket)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket 客户端断开连接: task_id={task_id}")
    
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        
    finally:
        # 清理连接
        if task_id:
            manager.disconnect(websocket, task_id)
