# tests/test_verifiers.py
import pytest
from ultimate_team.quality.gates import QualityGate, GateStatus
from ultimate_team.quality.verifiers import TestCoverageVerifier, TypeCheckVerifier

@pytest.mark.asyncio
async def test_test_coverage_verifier_pass():
    """测试测试覆盖率验证器（通过）"""
    gate = QualityGate(
        gate_id="test_coverage",
        name="测试覆盖率",
        description="确保 80% 覆盖率",
        threshold=80.0
    )

    verifier = TestCoverageVerifier()
    result = await verifier.verify(gate, coverage_data={"coverage": 85.0})

    assert result.status == GateStatus.PASSED
    assert "85.0%" in result.message

@pytest.mark.asyncio
async def test_test_coverage_verifier_fail():
    """测试测试覆盖率验证器（失败）"""
    gate = QualityGate(
        gate_id="test_coverage",
        name="测试覆盖率",
        description="确保 80% 覆盖率",
        threshold=80.0
    )

    verifier = TestCoverageVerifier()
    result = await verifier.verify(gate, coverage_data={"coverage": 65.0})

    assert result.status == GateStatus.FAILED
    assert "65.0%" in result.message

@pytest.mark.asyncio
async def test_type_check_verifier():
    """测试类型检查验证器"""
    gate = QualityGate(
        gate_id="type_check",
        name="类型检查",
        description="确保没有类型错误",
        threshold=0  # 零错误
    )

    verifier = TypeCheckVerifier()

    # 模拟无错误
    result = await verifier.verify(gate, type_errors=0)
    assert result.status == GateStatus.PASSED

    # 模拟有错误
    result = await verifier.verify(gate, type_errors=5)
    assert result.status == GateStatus.FAILED
