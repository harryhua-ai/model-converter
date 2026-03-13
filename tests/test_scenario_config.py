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
    assert "bug_fix" in scenarios
    assert "refactor" in scenarios
    assert "performance_optimization" in scenarios
    assert "urgent_release" in scenarios
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
    assert new_feature["priority"] == 30
    assert new_feature["strong_match"] is False
    assert "添加" in new_feature["triggers"]
    assert "planner" in new_feature["agents"]
    assert "architect" in new_feature["agents"]
    assert "B" in new_feature["closed_loops"]
    assert "E" in new_feature["closed_loops"]
    assert "F" in new_feature["closed_loops"]


def test_bugfix_scenario():
    """测试 bug_fix 场景配置"""
    scenarios = load_scenarios()
    bugfix = scenarios["bug_fix"]

    assert bugfix["name"] == "Bug修复"
    assert bugfix["priority"] == 20
    assert bugfix["strong_match"] is False
    assert "修复" in bugfix["triggers"]
    assert "coordinator" in bugfix["agents"]


def test_security_review_scenario():
    """测试 security_review 场景配置"""
    scenarios = load_scenarios()
    security = scenarios["security_review"]

    assert security["name"] == "安全审查"
    assert security["priority"] == 10
    assert security["strong_match"] is True
    assert "安全" in security["triggers"]
    assert "security-reviewer" in security["agents"]


def test_urgent_release_scenario():
    """测试 urgent_release 场景配置"""
    scenarios = load_scenarios()
    urgent = scenarios["urgent_release"]

    assert urgent["name"] == "紧急发布"
    assert urgent["priority"] == 1
    assert urgent["strong_match"] is False
    assert "紧急" in urgent["triggers"]
    assert "coordinator" in urgent["agents"]


def test_maintenance_scenario():
    """测试 maintenance 场景配置"""
    scenarios = load_scenarios()
    maintenance = scenarios["maintenance"]

    assert maintenance["name"] == "常规维护"
    assert maintenance["priority"] == 60
    assert maintenance.get("default") is None  # 不应该有 default 字段


def test_priority_ordering():
    """测试优先级排序（数字越小优先级越高）"""
    scenarios = load_scenarios()

    # 验证优先级范围
    priorities = {sid: config["priority"] for sid, config in scenarios.items()}

    # urgent_release 优先级最高 (1)
    assert priorities["urgent_release"] == 1
    # security_review 优先级第二 (10)
    assert priorities["security_review"] == 10
    # maintenance 优先级最低 (60)
    assert priorities["maintenance"] == 60


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
        # 支持多种时间格式：h, min, 分钟


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
