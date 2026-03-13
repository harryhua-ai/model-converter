# tests/test_base_loop.py
import pytest
from ultimate_team.loops.base_loop import BaseLoop, LoopStage, LoopState

class MockLoop(BaseLoop):
    """测试用闭环"""

    def _define_stages(self):
        return [
            LoopStage("stage1", "阶段1", ["条件1"]),
            LoopStage("stage2", "阶段2", ["条件2"])
        ]

    async def _execute_stage(self, stage, context):
        context["executed"] = context.get("executed", []) + [stage.stage_id]
        return context

def test_loop_initialization():
    """测试闭环初始化"""
    loop = MockLoop()
    assert loop.state == LoopState.IDLE
    assert loop.current_stage is None

def test_start_loop():
    """测试启动闭环"""
    loop = MockLoop()
    context = {}

    import asyncio
    result = asyncio.run(loop.start(context))

    assert loop.state == LoopState.COMPLETED
    assert result["executed"] == ["stage1", "stage2"]

def test_pause_and_resume():
    """测试暂停和恢复"""
    loop = MockLoop()

    # 先启动
    import asyncio
    asyncio.run(loop.start({}))

    # 现在测试暂停和恢复状态转换
    assert loop.state == LoopState.COMPLETED

    # 重置并测试暂停
    loop.reset()
    loop.state = LoopState.RUNNING
    loop.pause()
    assert loop.state == LoopState.PAUSED

    # 恢复
    loop.resume()
    assert loop.state == LoopState.RUNNING
