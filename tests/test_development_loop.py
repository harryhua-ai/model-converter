# tests/test_development_loop.py
import pytest
from ultimate_team.loops.development_loop import DevelopmentLoop

@pytest.mark.asyncio
async def test_development_loop_full_flow():
    """测试完整的开发闭环流程"""
    loop = DevelopmentLoop()

    context = {
        "feature_description": "添加用户登录功能",
        "test_framework": "pytest"
    }

    result = await loop.start(context)

    # 验证所有阶段都执行了
    assert "red_stage" in result
    assert "green_stage" in result
    assert "improve_stage" in result
    assert "review_stage" in result

    # 验证状态
    assert loop.is_completed()

@pytest.mark.asyncio
async def test_red_stage_writes_test():
    """测试 RED 阶段编写测试"""
    loop = DevelopmentLoop()

    context = {"feature_description": "测试功能"}
    result = await loop.start(context)

    assert result["red_stage"]["tests_written"] > 0
    assert result["red_stage"]["tests_passing"] == False

@pytest.mark.asyncio
async def test_green_stage_implements():
    """测试 GREEN 阶段实现功能"""
    loop = DevelopmentLoop()

    context = {"feature_description": "测试功能"}
    result = await loop.start(context)

    assert result["green_stage"]["implemented"] == True
    assert result["green_stage"]["tests_passing"] == True
