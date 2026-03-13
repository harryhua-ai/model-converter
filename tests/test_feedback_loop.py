# tests/test_feedback_loop.py
import pytest
from ultimate_team.loops.feedback_loop import FeedbackLoop

@pytest.mark.asyncio
async def test_feedback_loop_full_flow():
    """测试完整的反馈闭环流程"""
    loop = FeedbackLoop()

    context = {
        "issue_description": "用户报告登录失败",
        "logs": ["ERROR: Authentication failed"]
    }

    result = await loop.start(context)

    # 验证所有阶段
    assert "detect_stage" in result
    assert "analyze_stage" in result
    assert "fix_stage" in result
    assert "verify_stage" in result

@pytest.mark.asyncio
async def test_detect_stage():
    """测试问题检测阶段"""
    loop = FeedbackLoop()

    context = {"issue_description": "Bug 报告"}
    result = await loop.start(context)

    assert result["detect_stage"]["issue_detected"] == True
    assert "issue_type" in result["detect_stage"]
