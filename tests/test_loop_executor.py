# tests/test_loop_executor.py
import pytest
from ultimate_team.execution.loop_executor import LoopExecutor
from ultimate_team.loops.development_loop import DevelopmentLoop

@pytest.mark.asyncio
async def test_execute_development_loop():
    """测试执行开发闭环"""
    executor = LoopExecutor()

    loop = DevelopmentLoop()
    context = {"feature_description": "测试功能"}

    result = await executor.execute(loop, context)

    assert result["success"] == True
    assert "red_stage" in result["context"]

@pytest.mark.asyncio
async def test_execute_with_quality_gates():
    """测试带质量关卡的执行"""
    executor = LoopExecutor()

    loop = DevelopmentLoop()
    context = {"feature_description": "测试功能"}

    # 添加质量关卡
    from ultimate_team.quality import QualityGate, TestCoverageVerifier

    gate = QualityGate(
        gate_id="test_coverage",
        name="测试覆盖率",
        description="80% 覆盖率",
        threshold=80.0
    )

    verifier = TestCoverageVerifier()

    result = await executor.execute_with_gates(
        loop,
        context,
        quality_gates=[(gate, verifier, {"coverage_data": {"coverage": 85.0}})]
    )

    assert result["success"] == True
    assert result["quality_gate_results"][0]["status"] == "PASSED"
