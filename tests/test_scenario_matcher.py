# tests/test_scenario_matcher.py
import pytest
from ultimate_team.core.scenario_matcher import ScenarioMatcher

def test_scenario_match_exact_keywords():
    """测试精确关键词匹配"""
    matcher = ScenarioMatcher()

    # 测试 "添加" 触发 new_feature 场景
    result = matcher.match("添加批量转换功能")
    assert result["scenario_id"] == "new_feature"
    assert result["confidence"] > 0.8

def test_scenario_match_multiple_keywords():
    """测试多关键词匹配"""
    matcher = ScenarioMatcher()

    # 测试同时匹配多个关键词
    result = matcher.match("紧急修复安全问题")
    assert result["scenario_id"] == "security_review"  # 最高优先级
    assert result["matched_keywords"] == ["紧急", "安全"]

def test_scenario_match_no_match():
    """测试无匹配返回默认场景"""
    matcher = ScenarioMatcher()

    result = matcher.match("查看任务状态")
    assert result["scenario_id"] == "maintenance"  # 默认场景

def test_scenario_priority():
    """测试场景优先级排序（作为置信度相同时的决胜条件）"""
    matcher = ScenarioMatcher()

    # 测试场景：当多个场景有相同置信度时，选择优先级最高的
    # '优化性能问题' 同时匹配 refactor (priority=3) 和 performance (priority=8)
    # 两者都只匹配一个关键词，置信度相同，应选择 refactor（优先级数字更小）
    result = matcher.match("优化性能问题")

    # refactor 的关键词 '优化' 匹配，performance 的关键词 '性能' 也匹配
    # 两者置信度相同，但 refactor 优先级更高 (3 < 8)
    assert result["scenario_id"] == "refactor"
    assert result["confidence"] > 0
