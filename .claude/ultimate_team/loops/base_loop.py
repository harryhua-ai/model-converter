# .claude/ultimate_team/loops/base_loop.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Dict, Any, Optional

class LoopState(IntEnum):
    """闭环状态"""
    IDLE = 0       # 空闲
    RUNNING = 1    # 运行中
    PAUSED = 2     # 暂停
    COMPLETED = 3  # 已完成
    FAILED = 4     # 失败

@dataclass
class LoopStage:
    """闭环阶段"""
    stage_id: str                # 阶段 ID
    name: str                    # 阶段名称
    entry_conditions: List[str]  # 进入条件
    exit_conditions: List[str] = None  # 退出条件

    def __post_init__(self):
        if self.exit_conditions is None:
            self.exit_conditions = []

class BaseLoop(ABC):
    """闭环抽象基类"""

    def __init__(self):
        self.state = LoopState.IDLE
        self.current_stage: Optional[LoopStage] = None
        self.stages = self._define_stages()
        self.context: Dict[str, Any] = {}

    @abstractmethod
    def _define_stages(self) -> List[LoopStage]:
        """定义闭环阶段"""
        pass

    @abstractmethod
    async def _execute_stage(self, stage: LoopStage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个阶段"""
        pass

    async def start(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """启动闭环"""
        if context is None:
            context = {}

        self.context = context
        self.state = LoopState.RUNNING

        try:
            for stage in self.stages:
                if self.state == LoopState.PAUSED:
                    break

                self.current_stage = stage

                # 检查进入条件
                if not self._check_entry_conditions(stage):
                    raise ValueError(f"Stage {stage.stage_id} entry conditions not met")

                # 执行阶段
                self.context = await self._execute_stage(stage, self.context)

                # 检查退出条件
                if not self._check_exit_conditions(stage):
                    raise ValueError(f"Stage {stage.stage_id} exit conditions not met")

            self.state = LoopState.COMPLETED
            return self.context

        except Exception as e:
            self.state = LoopState.FAILED
            self.context["error"] = str(e)
            raise

    def pause(self) -> None:
        """暂停闭环"""
        if self.state == LoopState.RUNNING:
            self.state = LoopState.PAUSED

    def resume(self) -> None:
        """恢复闭环"""
        if self.state == LoopState.PAUSED:
            self.state = LoopState.RUNNING

    def reset(self) -> None:
        """重置闭环"""
        self.state = LoopState.IDLE
        self.current_stage = None
        self.context = {}

    def _check_entry_conditions(self, stage: LoopStage) -> bool:
        """检查进入条件"""
        # 默认实现：总是通过
        # 子类可以覆盖以实现特定条件检查
        return True

    def _check_exit_conditions(self, stage: LoopStage) -> bool:
        """检查退出条件"""
        # 默认实现：总是通过
        # 子类可以覆盖以实现特定条件检查
        return True
