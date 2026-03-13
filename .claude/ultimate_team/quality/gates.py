# .claude/ultimate-team/quality/gates.py
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Dict, Any

class GateStatus(IntEnum):
    """关卡状态"""
    PENDING = 0     # 待验证
    PASSED = 1      # 通过
    FAILED = 2      # 失败
    WARNING = 3     # 警告
    SKIPPED = 4     # 跳过

@dataclass
class QualityGate:
    """质量关卡定义"""
    gate_id: str              # 关卡唯一标识
    name: str                 # 关卡名称
    description: str          # 描述
    threshold: float          # 阈值
    critical: bool = True     # 是否关键关卡（失败则阻断）
    metadata: Dict[str, Any] = None  # 额外元数据

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class GateResult:
    """关卡验证结果"""
    gate_id: str              # 关卡 ID
    status: GateStatus        # 状态
    actual_value: float       # 实际值
    threshold: float          # 阈值
    message: str              # 消息
    details: Dict[str, Any] = None  # 详细信息

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def is_passed(self) -> bool:
        """是否通过"""
        return self.status == GateStatus.PASSED

    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == GateStatus.FAILED

    def is_warning(self) -> bool:
        """是否警告"""
        return self.status == GateStatus.WARNING

    def should_block(self) -> bool:
        """是否应该阻断流程"""
        return self.status == GateStatus.FAILED
