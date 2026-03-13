# tests/test_full_process_loop.py
import pytest
from ultimate_team.loops.full_process_loop import FullProcessLoop

@pytest.mark.asyncio
async def test_full_process_loop():
    """测试完整的 9 阶段流程"""
    loop = FullProcessLoop()

    context = {
        "requirement": "实现用户认证系统",
        "team_size": 3
    }

    result = await loop.start(context)

    # 验证 9 个阶段都执行了
    expected_stages = [
        "requirements",
        "design",
        "implementation",
        "testing",
        "review",
        "documentation",
        "deployment",
        "monitoring",
        "maintenance"
    ]

    for stage in expected_stages:
        assert stage + "_stage" in result

@pytest.mark.asyncio
async def test_stage_dependencies():
    """测试阶段依赖关系"""
    loop = FullProcessLoop()

    context = {"requirement": "简单功能"}
    result = await loop.start(context)

    # 验证阶段按顺序执行
    assert result["requirements_stage"]["completed_before"] == []
    assert result["design_stage"]["completed_before"] == ["requirements"]
