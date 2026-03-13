# tests/test_quality_gates.py
import pytest
from ultimate_team.quality.gates import QualityGate, GateStatus, GateResult

def test_create_quality_gate():
    """测试创建质量关卡"""
    gate = QualityGate(
        gate_id="test_coverage",
        name="测试覆盖率",
        description="确保代码测试覆盖率达到 80% 以上",
        threshold=80.0
    )

    assert gate.gate_id == "test_coverage"
    assert gate.name == "测试覆盖率"
    assert gate.threshold == 80.0

def test_gate_result_pass():
    """测试关卡通过"""
    result = GateResult(
        gate_id="test_coverage",
        status=GateStatus.PASSED,
        actual_value=85.0,
        threshold=80.0,
        message="测试覆盖率为 85.0%，通过关卡"
    )

    assert result.status == GateStatus.PASSED
    assert result.is_passed()
    assert not result.is_failed()

def test_gate_result_fail():
    """测试关卡失败"""
    result = GateResult(
        gate_id="test_coverage",
        status=GateStatus.FAILED,
        actual_value=65.0,
        threshold=80.0,
        message="测试覆盖率为 65.0%，未达到 80% 要求"
    )

    assert result.status == GateStatus.FAILED
    assert result.is_failed()
    assert not result.is_passed()

def test_gate_result_warning():
    """测试关卡警告"""
    result = GateResult(
        gate_id="test_coverage",
        status=GateStatus.WARNING,
        actual_value=78.0,
        threshold=80.0,
        message="测试覆盖率为 78.0%，接近但未达到 80% 要求"
    )

    assert result.status == GateStatus.WARNING
