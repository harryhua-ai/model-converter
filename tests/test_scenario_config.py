# tests/test_scenario_config.py
"""测试场景配置加载功能"""
import pytest
import yaml
from ultimate_team.scenarios import load_scenarios


def test_load_scenarios():
    """测试加载场景配置"""
    scenarios = load_scenarios()

    # 验证所有8种场景都存在
    assert "new_feature" in scenarios
    assert "bugfix" in scenarios
    assert "refactor" in scenarios
    assert "performance" in scenarios
    assert "testing" in scenarios
    assert "security_review" in scenarios
    assert "documentation" in scenarios
    assert "maintenance" in scenarios

    assert len(scenarios) == 8


def test_scenario_structure():
    """测试场景配置结构完整性"""
    scenarios = load_scenarios()

    # 验证每个场景都包含必需的字段
    required_fields = [
        'name', 'triggers', 'priority', 'strong_match',
        'agents', 'skills', 'closed_loops', 'estimated_time'
    ]

    for scenario_id, config in scenarios.items():
        for field in required_fields:
            assert field in config, f"场景 {scenario_id} 缺少字段: {field}"


def test_new_feature_scenario():
    """测试 new_feature 场景配置"""
    scenarios = load_scenarios()
    new_feature = scenarios["new_feature"]

    assert new_feature["name"] == "新功能开发"
    assert new_feature["priority"] == 1
    assert new_feature["strong_match"] is True
    assert "添加" in new_feature["triggers"]
    assert "planner" in new_feature["agents"]
    assert "architect" in new_feature["agents"]
    assert "B" in new_feature["closed_loops"]
    assert "E" in new_feature["closed_loops"]
    assert "F" in new_feature["closed_loops"]


def test_bugfix_scenario():
    """测试 bugfix 场景配置"""
    scenarios = load_scenarios()
    bugfix = scenarios["bugfix"]

    assert bugfix["name"] == "Bug修复"
    assert bugfix["priority"] == 2
    assert bugfix["strong_match"] is False
    assert "修复" in bugfix["triggers"]
    assert "tdd-guide" in bugfix["agents"]


def test_security_review_scenario():
    """测试 security_review 场景配置"""
    scenarios = load_scenarios()
    security = scenarios["security_review"]

    assert security["name"] == "安全审查"
    assert security["priority"] == 6
    assert security["strong_match"] is True
    assert "安全" in security["triggers"]
    assert "security-reviewer" in security["agents"]


def test_maintenance_scenario_default():
    """测试 maintenance 场景的默认标记"""
    scenarios = load_scenarios()
    maintenance = scenarios["maintenance"]

    assert maintenance["name"] == "常规维护"
    assert maintenance["priority"] == 8
    assert maintenance.get("default") is True


def test_priority_ordering():
    """测试优先级排序（数字越小优先级越高）"""
    scenarios = load_scenarios()

    # 验证优先级范围
    priorities = [config["priority"] for config in scenarios.values()]
    assert min(priorities) == 1  # new_feature
    assert max(priorities) == 8  # maintenance


def test_closed_loops_values():
    """测试所有闭环类型都是有效的"""
    scenarios = load_scenarios()
    valid_loops = {'B', 'E', 'F'}

    for scenario_id, config in scenarios.items():
        for loop in config["closed_loops"]:
            assert loop in valid_loops, \
                f"场景 {scenario_id} 包含无效的闭环类型: {loop}"


def test_agents_and_skills_lists():
    """测试 agents 和 skills 字段是列表类型"""
    scenarios = load_scenarios()

    for scenario_id, config in scenarios.items():
        assert isinstance(config["agents"], list), \
            f"场景 {scenario_id} 的 agents 字段不是列表"
        assert isinstance(config["skills"], list), \
            f"场景 {scenario_id} 的 skills 字段不是列表"


def test_estimated_time_format():
    """测试预估时间格式"""
    scenarios = load_scenarios()

    for scenario_id, config in scenarios.items():
        time_str = config["estimated_time"]
        assert isinstance(time_str, str), \
            f"场景 {scenario_id} 的 estimated_time 不是字符串"
        assert "分钟" in time_str or "min" in time_str, \
            f"场景 {scenario_id} 的时间格式不正确: {time_str}"


def test_yaml_file_validity():
    """测试 YAML 文件语法正确性"""
    import os
    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        ".claude",
        "ultimate_team",
        "scenarios",
        "scenarios.yaml"
    )

    # 验证文件可以正确解析
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict)
    assert len(data) == 8
