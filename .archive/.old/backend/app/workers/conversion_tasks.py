"""
Celery 任务定义
模型转换的后台任务
"""
import os
import traceback
from pathlib import Path

from celery import Task
from loguru import logger as celery_logger

from app.celery_app import celery_app
from app.services.conversion import ConversionService
from app.services.task_manager import TaskManager
from app.models.schemas import TaskStatus


class ConversionTaskWithCallback(Task):
    """带回调的转换任务基类"""

    _task_manager = None

    @property
    def task_manager(self):
        """延迟初始化 TaskManager（避免序列化问题）"""
        if self._task_manager is None:
            self._task_manager = TaskManager()
        return self._task_manager

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        celery_logger.info(f"任务完成", task_id=task_id)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        error_msg = f"{type(exc).__name__}: {str(exc)}"
        celery_logger.error(f"任务失败", task_id=task_id, error=error_msg, traceback=traceback.format_exc())

        # 更新任务状态为失败
        try:
            self.task_manager.update_task(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=error_msg,
            )
        except Exception as e:
            celery_logger.error(f"更新失败状态时出错", task_id=task_id, error=str(e))


@celery_app.task(
    bind=True,
    base=ConversionTaskWithCallback,
    name="app.workers.conversion_tasks.convert_model_task",
    max_retries=0,  # 转换任务不自动重试
)
def convert_model_task(self, task_id: str, input_path: str, config_dict: dict, **kwargs):
    """
    模型转换任务（Celery 后台执行）

    Args:
        task_id: 任务 ID
        input_path: 输入模型路径
        config_dict: 转换配置字典（避免序列化问题）
        **kwargs: 其他参数（calibration_dataset_path, class_yaml_path）

    Returns:
        str: 输出文件名
    """
    from app.models.schemas import ConversionConfig
    from app.core.config import settings

    celery_logger.info(f"开始转换任务", task_id=task_id, input_path=input_path)

    try:
        # 重建配置对象
        config = ConversionConfig(**config_dict)

        # 初始化转换服务
        conversion_service = ConversionService()

        # 执行转换（注意：这是在 Worker 进程中执行，不会阻塞 API）
        import asyncio

        # 创建新的事件循环（Celery Worker 没有运行中的事件循环）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 运行异步转换函数
            loop.run_until_complete(
                conversion_service.convert_model(
                    task_id=task_id,
                    input_path=input_path,
                    config=config,
                    **kwargs,
                )
            )
        finally:
            loop.close()

        # 获取输出文件名
        task_manager = self.task_manager
        # 这里需要从某个地方获取输出文件名，暂时返回成功标记
        return f"task_{task_id}_completed"

    except Exception as e:
        celery_logger.error(
            f"转换任务执行失败",
            task_id=task_id,
            error=str(e),
            traceback=traceback.format_exc(),
        )
        # 重新抛出异常，让 Celery 的失败处理机制生效
        raise


@celery_app.task(
    bind=True,
    name="app.workers.conversion_tasks.health_check_task",
)
def health_check_task(self):
    """健康检查任务"""
    return {"status": "healthy", "worker": "celery"}
