"""
性能监控模块

记录各步骤耗时、统计缓存命中率、监控资源使用
"""

import logging
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class StepMetrics:
    """步骤指标"""
    step_name: str
    duration_ms: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    """任务指标"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: int = 0
    steps: List[StepMetrics] = field(default_factory=list)
    cache_hit: bool = False
    model_size_bytes: int = 0
    output_size_bytes: int = 0


class PerformanceMonitor:
    """性能监控器（单例）"""

    _instance: Optional['PerformanceMonitor'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.step_aggregates: Dict[str, List[int]] = defaultdict(list)
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.cache_hits = 0
        self._initialized = True
        logger.info("性能监控器初始化完成")

    def start_task(self, task_id: str) -> None:
        """开始任务监控

        Args:
            task_id: 任务 ID
        """
        self.task_metrics[task_id] = TaskMetrics(
            task_id=task_id,
            start_time=datetime.now()
        )
        self.total_tasks += 1
        logger.debug(f"开始监控任务: {task_id}")

    def end_task(
        self,
        task_id: str,
        success: bool,
        model_size: int = 0,
        output_size: int = 0
    ) -> None:
        """结束任务监控

        Args:
            task_id: 任务 ID
            success: 是否成功
            model_size: 模型大小（字节）
            output_size: 输出大小（字节）
        """
        if task_id not in self.task_metrics:
            return

        metrics = self.task_metrics[task_id]
        metrics.end_time = datetime.now()
        metrics.total_duration_ms = int(
            (metrics.end_time - metrics.start_time).total_seconds() * 1000
        )
        metrics.model_size_bytes = model_size
        metrics.output_size_bytes = output_size

        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        logger.info(
            f"任务完成: {task_id} "
            f"(耗时: {metrics.total_duration_ms}ms, "
            f"成功: {success})"
        )

    def record_step(
        self,
        task_id: str,
        step_name: str,
        duration_ms: int,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录步骤指标

        Args:
            task_id: 任务 ID
            step_name: 步骤名称
            duration_ms: 耗时（毫秒）
            success: 是否成功
            error_message: 错误信息
            metadata: 额外元数据
        """
        if task_id not in self.task_metrics:
            self.start_task(task_id)

        step_metrics = StepMetrics(
            step_name=step_name,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )

        self.task_metrics[task_id].steps.append(step_metrics)
        self.step_aggregates[step_name].append(duration_ms)

        logger.debug(
            f"步骤完成: {task_id}/{step_name} "
            f"(耗时: {duration_ms}ms, 成功: {success})"
        )

    def record_cache_hit(self, task_id: str) -> None:
        """记录缓存命中

        Args:
            task_id: 任务 ID
        """
        if task_id in self.task_metrics:
            self.task_metrics[task_id].cache_hit = True
            self.cache_hits += 1

    @contextmanager
    def measure_step(
        self,
        task_id: str,
        step_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """测量步骤耗时的上下文管理器

        Args:
            task_id: 任务 ID
            step_name: 步骤名称
            metadata: 额外元数据

        Yields:
            None

        Example:
            with monitor.measure_step(task_id, "export_tflite"):
                # 执行步骤
                export_tflite()
        """
        start_time = time.time()
        success = True
        error_message = None

        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            self.record_step(
                task_id=task_id,
                step_name=step_name,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                metadata=metadata
            )

    def get_task_metrics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务指标

        Args:
            task_id: 任务 ID

        Returns:
            任务指标字典
        """
        if task_id not in self.task_metrics:
            return None

        metrics = self.task_metrics[task_id]
        return {
            'task_id': metrics.task_id,
            'start_time': metrics.start_time.isoformat(),
            'end_time': metrics.end_time.isoformat() if metrics.end_time else None,
            'total_duration_ms': metrics.total_duration_ms,
            'cache_hit': metrics.cache_hit,
            'model_size_mb': round(metrics.model_size_bytes / (1024 * 1024), 2),
            'output_size_mb': round(metrics.output_size_bytes / (1024 * 1024), 2),
            'steps': [
                {
                    'step_name': s.step_name,
                    'duration_ms': s.duration_ms,
                    'success': s.success,
                    'error_message': s.error_message
                }
                for s in metrics.steps
            ]
        }

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """获取聚合统计

        Returns:
            聚合统计字典
        """
        step_stats = {}
        for step_name, durations in self.step_aggregates.items():
            if durations:
                step_stats[step_name] = {
                    'count': len(durations),
                    'avg_ms': round(sum(durations) / len(durations), 2),
                    'min_ms': min(durations),
                    'max_ms': max(durations),
                    'total_ms': sum(durations)
                }

        total_requests = self.successful_tasks + self.failed_tasks
        success_rate = (
            (self.successful_tasks / total_requests * 100)
            if total_requests > 0 else 0
        )
        cache_hit_rate = (
            (self.cache_hits / self.total_tasks * 100)
            if self.total_tasks > 0 else 0
        )

        return {
            'total_tasks': self.total_tasks,
            'successful_tasks': self.successful_tasks,
            'failed_tasks': self.failed_tasks,
            'success_rate': round(success_rate, 2),
            'cache_hits': self.cache_hits,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'step_statistics': step_stats
        }

    def cleanup_old_tasks(self, max_tasks: int = 1000) -> int:
        """清理旧任务记录

        Args:
            max_tasks: 保留的最大任务数

        Returns:
            清理的任务数量
        """
        if len(self.task_metrics) <= max_tasks:
            return 0

        # 按开始时间排序
        sorted_tasks = sorted(
            self.task_metrics.items(),
            key=lambda x: x[1].start_time
        )

        # 保留最新的任务
        tasks_to_remove = len(sorted_tasks) - max_tasks
        for task_id, _ in sorted_tasks[:tasks_to_remove]:
            del self.task_metrics[task_id]

        logger.info(f"清理了 {tasks_to_remove} 个旧任务记录")
        return tasks_to_remove


# 全局性能监控器实例
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器单例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor