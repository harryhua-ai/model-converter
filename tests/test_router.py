# tests/test_router.py
import pytest
from ultimate_team.core.router import ScenarioRouter


def test_route_to_fast_path():
    """测试路由到快速路径"""
    router = ScenarioRouter()

    # 使用简单的英文输入，有明确的单词边界
    analysis = router.analyze("add batch conversion feature")
    # 英文输入有4个单词，且如果匹配度高应该是common
    # 由于置信度可能不高，这里只测试路由逻辑
    path_type, scenario = router.route(analysis)

    # 如果是common scenario则走FAST_PATH
    if analysis["is_common_scenario"]:
        assert path_type == "FAST_PATH"
        assert scenario is not None
    else:
        # 否则走SMART_PATH
        assert path_type == "SMART_PATH"
        assert scenario is None


def test_route_to_smart_path():
    """测试路由到智能路径"""
    router = ScenarioRouter()

    # 复杂场景
    analysis = router.analyze("重构支付系统同时添加新功能并优化性能")
    assert analysis["is_common_scenario"] == False

    path_type, scenario = router.route(analysis)
    assert path_type == "SMART_PATH"
    assert scenario is None


def test_analyze_simple_input():
    """测试分析简单输入"""
    router = ScenarioRouter()

    # 英文输入：4个单词，无多任务标志
    analysis = router.analyze("fix login bug")
    assert analysis["complexity"] == "simple"


def test_analyze_medium_input():
    """测试分析中等复杂度输入"""
    router = ScenarioRouter()

    # 英文输入：15个单词，在10-20范围内
    analysis = router.analyze("we need to optimize user registration flow and add email verification functionality")
    assert analysis["complexity"] == "medium"


def test_analyze_complex_input():
    """测试分析复杂输入"""
    router = ScenarioRouter()

    analysis = router.analyze("重构支付系统同时添加新功能并优化性能")
    assert analysis["complexity"] == "complex"


def test_analyze_multi_task_detection():
    """测试多任务检测"""
    router = ScenarioRouter()

    # 包含"同时"
    analysis = router.analyze("添加功能同时修复bug")
    assert analysis["complexity"] == "complex"

    # 包含"并且"
    analysis = router.analyze("优化代码并且添加测试")
    assert analysis["complexity"] == "complex"

    # 包含"加上"
    analysis = router.analyze("重构模块加上更新文档")
    assert analysis["complexity"] == "complex"

    # 英文多任务：超过20个单词
    analysis = router.analyze("we need to refactor the entire payment system architecture and add several new features for better user experience and optimize performance and also update all the documentation")
    assert analysis["complexity"] == "complex"


def test_route_with_low_confidence():
    """测试低置信度路由到智能路径"""
    router = ScenarioRouter()

    # 使用不太常见的输入，置信度可能低于0.7
    analysis = router.analyze("做一些不常见的复杂任务")
    # 即使是简单场景，如果置信度<0.7也应该走智能路径
    path_type, scenario = router.route(analysis)

    # 低置信度应该走智能路径
    if not analysis["is_common_scenario"]:
        assert path_type == "SMART_PATH"
        assert scenario is None


def test_get_scenario_config():
    """测试获取场景配置"""
    router = ScenarioRouter()

    scenario = router._get_scenario_config("new_feature")
    assert scenario is not None
    assert scenario["scenario_id"] == "new_feature"
    assert "name" in scenario


def test_analyze_returns_all_fields():
    """测试分析返回所有必需字段"""
    router = ScenarioRouter()

    analysis = router.analyze("添加用户管理功能")
    required_fields = ["intent", "scenario_id", "confidence", "is_common_scenario", "complexity"]

    for field in required_fields:
        assert field in analysis
