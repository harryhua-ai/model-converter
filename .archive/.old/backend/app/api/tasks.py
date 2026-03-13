"""
任务管理 API 端点
提供任务查询和监控功能
"""
import os
from typing import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from celery.result import AsyncResult
import structlog

from app.models.schemas import ConversionTask, TaskListResponse, TaskStatus
from app.services.task_manager import get_task_manager
from app.celery_app import celery_app

router = APIRouter()
logger = structlog.get_logger(__name__)
task_manager = get_task_manager()


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> TaskListResponse:
    """
    获取任务列表

    Args:
        status: 过滤状态（可选）
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        TaskListResponse: 任务列表
    """
    tasks = await task_manager.list_tasks(status=status, limit=limit, offset=offset)
    total = await task_manager.count_tasks(status=status)

    return TaskListResponse(tasks=tasks, total=total)


@router.get("/{task_id}", response_model=ConversionTask)
async def get_task(task_id: str) -> ConversionTask:
    """
    获取任务详情

    Args:
        task_id: 任务 ID

    Returns:
        ConversionTask: 任务详情

    Raises:
        HTTPException: 任务不存在
    """
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str) -> dict[str, str]:
    """
    取消正在进行的任务

    Args:
        task_id: 任务 ID

    Returns:
        dict: 取消结果

    Raises:
        HTTPException: 任务不存在或无法取消
    """
    from app.celery_app import celery_app

    # 获取任务状态
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查任务是否可以取消
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"任务无法取消（当前状态：{task.status.value}）"
        )

    # 尝试通过 Celery 撤销任务
    try:
        # 使用 revoke 终止任务（terminate=True 会发送 SIGTERM）
        celery_app.control.revoke(task_id, terminate=True, signal='SIGTERM')
        logger.info("已发送 Celery 任务撤销请求", task_id=task_id)
    except Exception as e:
        logger.warning("Celery 任务撤销失败", task_id=task_id, error=str(e))

    # 更新任务状态为已取消
    cancelled_task = await task_manager.cancel_task(task_id)

    # 清理临时文件
    try:
        import shutil
        from app.core.config import settings

        work_dir = os.path.join(settings.TEMP_DIR, task_id)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
            logger.info("已清理临时文件", task_id=task_id, path=work_dir)
    except Exception as e:
        logger.warning("清理临时文件失败", task_id=task_id, error=str(e))

    return {
        "message": f"任务 {task_id} 已取消",
        "task_id": task_id,
        "previous_status": task.status.value
    }


@router.websocket("/ws/tasks/{task_id}/progress")
async def websocket_task_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket 端点：实时推送任务进度

    Args:
        websocket: WebSocket 连接
        task_id: 任务 ID
    """
    await websocket.accept()
    logger.info("WebSocket 连接建立", task_id=task_id)

    try:
        # 发送初始状态
        task = await task_manager.get_task(task_id)
        if not task:
            await websocket.send_json({"error": "任务不存在"})
            await websocket.close()
            return

        await websocket.send_json(task.model_dump())

        # 订阅任务更新
        async for update in task_manager.subscribe_task_updates(task_id):
            await websocket.send_json(update)

    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开", task_id=task_id)
    except Exception as e:
        logger.error("WebSocket 错误", task_id=task_id, error=str(e))
        await websocket.close(code=1011, reason=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: str) -> dict[str, str]:
    """
    删除任务和相关文件

    Args:
        task_id: 任务 ID

    Returns:
        dict: 删除结果
    """
    success = await task_manager.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {"message": f"任务 {task_id} 已删除"}
