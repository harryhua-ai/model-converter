# tests/integration/test_routing_integration.py
import pytest
from ultimate_team.core.router import ScenarioRouter


def test_full_routing_flow():
    """测试完整的路由流程

    验证路由系统在不同场景下的路径决策：
    1. 高置信度简单场景 → FAST_PATH（使用预设配置）
    2. 复杂多任务场景 → SMART_PATH（需要动态规划）
    """
    router = ScenarioRouter()

    # 测试高置信度的简单请求
    # "修复fix bug错误" 匹配 bug_fix 的所有触发词，置信度 = 1.0 (> 0.7)
    # 且复杂度为 simple，因此是常见场景 → FAST_PATH
    analysis1 = router.analyze("修复fix bug错误")
    assert analysis1["is_common_scenario"] == True
    assert analysis1["scenario_id"] == "bug_fix"
    assert analysis1["confidence"] == 1.0
    assert analysis1["complexity"] == "simple"

    path1, scenario1 = router.route(analysis1)
    assert path1 == "FAST_PATH"
    assert scenario1 is not None
    assert scenario1["name"] == "Bug修复"

    # 测试复杂的多任务请求
    # "重构认证系统同时优化数据库性能" 包含"同时"（多任务标志）
    # 复杂度 = "complex"，无论置信度如何都不是常见场景 → SMART_PATH
    analysis2 = router.analyze("重构认证系统同时优化数据库性能")
    assert analysis2["is_common_scenario"] == False
    assert analysis2["complexity"] == "complex"

    path2, scenario2 = router.route(analysis2)
    assert path2 == "SMART_PATH"
    assert scenario2 is None
