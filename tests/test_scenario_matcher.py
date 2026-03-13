# tests/test_scenario_matcher.py
import pytest
from ultimate_team.core.scenario_matcher import ScenarioMatcher

def test_scenario_match_exact_keywords():
    """测试精确关键词匹配"""
    matcher = ScenarioMatcher()

    # 测试 "添加" 触发 new_feature 场景
    result = matcher.match("添加批量转换功能")
    assert result["scenario_id"] == "new_feature"
    # "添加" 匹配 new_feature 的 3 个触发词之一，置信度为 1/3
    assert result["confidence"] > 0.3

def test_scenario_match_multiple_keywords():
    """测试多关键词匹配"""
    matcher = ScenarioMatcher()

    # 测试同时匹配多个关键词
    # "紧急" 匹配 urgent_release (priority=1), "安全" 匹配 security_review (priority=10)
    # 两者置信度相同（都匹配1个触发词），但 urgent_release 优先级更高
    result = matcher.match("紧急修复安全问题")
    assert result["scenario_id"] == "urgent_release"  # 优先级 1 > 10
    assert result["confidence"] > 0


def test_scenario_match_urgent_release():
    """测试紧急发布场景匹配"""
    matcher = ScenarioMatcher()

    result = matcher.match("紧急发布 hotfix")
    assert result["scenario_id"] == "urgent_release"
    assert result["confidence"] > 0

def test_scenario_match_no_match():
    """测试无匹配返回默认场景"""
    matcher = ScenarioMatcher()

    result = matcher.match("查看任务状态")
    # 现在没有默认场景，应该返回 None 或 maintenance
    assert result["scenario_id"] in ["maintenance", None]

def test_scenario_priority():
    """测试场景优先级排序（作为置信度相同时的决胜条件）"""
    matcher = ScenarioMatcher()

    # 测试场景：当多个场景有相同置信度时，选择优先级最高的
    # '优化性能问题' 同时匹配 refactor (priority=40) 和 performance_optimization (priority=50)
    # 但是 "优化" 在 refactor 的触发词 "优化代码" 中，不能直接匹配
    # "性能" 在 performance_optimization 的触发词 "性能" 中，可以直接匹配
    # 所以应该匹配 performance_optimization
    result = matcher.match("优化性能问题")

    # "性能" 可以直接匹配 performance_optimization 的触发词
    assert result["scenario_id"] == "performance_optimization"
    assert result["confidence"] > 0
