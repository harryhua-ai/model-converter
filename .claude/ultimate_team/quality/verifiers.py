# .claude/ultimate_team/quality/verifiers.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from .gates import QualityGate, GateResult, GateStatus

class BaseVerifier(ABC):
    """验证器抽象基类"""

    @abstractmethod
    async def verify(self, gate: QualityGate, **kwargs) -> GateResult:
        """执行验证"""
        pass

class TestCoverageVerifier(BaseVerifier):
    """测试覆盖率验证器"""

    async def verify(self, gate: QualityGate, **kwargs) -> GateResult:
        """验证测试覆盖率"""
        coverage = kwargs.get("coverage_data", {}).get("coverage", 0.0)

        if coverage >= gate.threshold:
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.PASSED,
                actual_value=coverage,
                threshold=gate.threshold,
                message=f"测试覆盖率为 {coverage:.1f}%，达到 {gate.threshold:.1f}% 要求"
            )
        elif coverage >= gate.threshold - 10:
            # 接近阈值，警告
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.WARNING,
                actual_value=coverage,
                threshold=gate.threshold,
                message=f"测试覆盖率为 {coverage:.1f}%，接近但未达到 {gate.threshold:.1f}% 要求"
            )
        else:
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.FAILED,
                actual_value=coverage,
                threshold=gate.threshold,
                message=f"测试覆盖率为 {coverage:.1f}%，未达到 {gate.threshold:.1f}% 要求"
            )

class TypeCheckVerifier(BaseVerifier):
    """类型检查验证器"""

    async def verify(self, gate: QualityGate, **kwargs) -> GateResult:
        """验证类型检查"""
        errors = kwargs.get("type_errors", 0)

        if errors == 0:
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.PASSED,
                actual_value=0,
                threshold=gate.threshold,
                message=f"类型检查通过，无错误"
            )
        else:
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.FAILED,
                actual_value=errors,
                threshold=gate.threshold,
                message=f"发现 {errors} 个类型错误",
                details={"error_count": errors}
            )

class LintVerifier(BaseVerifier):
    """代码检查验证器"""

    async def verify(self, gate: QualityGate, **kwargs) -> GateResult:
        """验证代码检查结果"""
        errors = kwargs.get("lint_errors", 0)
        warnings = kwargs.get("lint_warnings", 0)

        if errors == 0:
            status = GateStatus.PASSED if warnings < 10 else GateStatus.WARNING
            return GateResult(
                gate_id=gate.gate_id,
                status=status,
                actual_value=errors + warnings,
                threshold=gate.threshold,
                message=f"代码检查通过：{errors} 错误，{warnings} 警告"
            )
        else:
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.FAILED,
                actual_value=errors,
                threshold=gate.threshold,
                message=f"代码检查失败：发现 {errors} 个错误",
                details={"error_count": errors, "warning_count": warnings}
            )

class SecurityVerifier(BaseVerifier):
    """安全检查验证器"""

    async def verify(self, gate: QualityGate, **kwargs) -> GateResult:
        """验证安全检查结果"""
        critical_issues = kwargs.get("critical_security_issues", 0)

        if critical_issues == 0:
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.PASSED,
                actual_value=0,
                threshold=gate.threshold,
                message=f"安全检查通过，无关键安全问题"
            )
        else:
            return GateResult(
                gate_id=gate.gate_id,
                status=GateStatus.FAILED,
                actual_value=critical_issues,
                threshold=gate.threshold,
                message=f"安全检查失败：发现 {critical_issues} 个关键安全问题",
                details={"critical_issues": critical_issues}
            )
