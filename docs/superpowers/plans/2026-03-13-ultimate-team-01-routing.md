# Ultimate Team - Part 1: 核心路由系统实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建智能场景路由系统，支持 8 种预设场景的快速匹配和复杂场景的 AI 决策

**Architecture:** 基于混合架构，场景路由器分析用户输入，80% 常见场景走快速路径（预设规则），20% 复杂场景走智能路径（AI 决策）

**Tech Stack:** Python 3.11+, YAML (配置), Regular Expressions (匹配)

---

## 文件结构

```
.claude/
├── skills/
│   └── ultimate-team.py          # 主入口
├── ultimate-team/
│   ├── core/
│   │   ├── router.py             # 场景路由器
│   │   ├── scenario_matcher.py   # 场景匹配器
│   │   └── path_selector.py      # 路径选择器
│   ├── scenarios/
│   │   ├── scenarios.yaml        # 8 种预设场景配置
│   │   └── __init__.py
│   └── smart_path/
│       ├── ai_analyzer.py        # AI 场景分析器
│       └── resource_matcher.py   # 动态资源匹配器
└── tests/
    ├── test_router.py
    ├── test_scenario_matcher.py
    └── test_path_selector.py
```

---

## Chunk 1: 场景匹配器

### Task 1: 创建场景匹配器核心逻辑

**Files:**
- Create: `.claude/ultimate-team/core/scenario_matcher.py`
- Create: `tests/test_scenario_matcher.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario_matcher.py -v`
Expected: FAIL with "ScenarioMatcher not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/core/scenario_matcher.py
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class MatchResult:
    """匹配结果"""
    scenario_id: str
    confidence: float
    matched_keywords: List[str]

class ScenarioMatcher:
    """场景匹配器 - 匹配用户输入到预设场景"""

    def __init__(self):
        # 从配置文件加载场景定义
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> Dict:
        """加载场景配置"""
        import yaml
        config_path = ".claude/ultimate-team/scenarios/scenarios.yaml"
        with open(config_path) as f:
            return yaml.safe_load(f)

    def match(self, user_input: str) -> MatchResult:
        """匹配用户输入到场景"""
        best_match = None
        best_confidence = 0.0
        matched_keywords = []

        for scenario_id, config in self.scenarios.items():
            # 检查触发词
            matches = []
            for trigger in config["triggers"]:
                if trigger in user_input:
                    matches.append(trigger)

            if not matches:
                continue

            # 计算匹配置信度
            confidence = len(matches) / len(config["triggers"])

            # 强匹配加分
            if config.get("strong_match"):
                for trigger in matches:
                    if user_input.startswith(trigger):
                        confidence += 0.3

            if confidence > best_confidence:
                best_match = scenario_id
                best_confidence = confidence
                matched_keywords = matches

        # 无匹配返回默认场景
        if best_match is None:
            best_match = "maintenance"
            best_confidence = 1.0
            matched_keywords = []

        return MatchResult(
            scenario_id=best_match,
            confidence=best_confidence,
            matched_keywords=matched_keywords
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario_matcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_scenario_matcher.py .claude/ultimate-team/core/scenario_matcher.py
git commit -m "feat: add scenario matcher core logic"
```

---

### Task 2: 实现场景优先级排序

**Files:**
- Modify: `.claude/ultimate-team/core/scenario_matcher.py`
- Modify: `tests/test_scenario_matcher.py`

- [ ] **Step 1: Add priority test**

```python
def test_scenario_priority():
    """测试场景优先级排序"""
    matcher = ScenarioMatcher()

    # 测试同时匹配多个场景时的优先级
    result = matcher.match("紧急修复安全问题")
    # security_review 应该有最高优先级
    assert result["scenario_id"] == "security_review"
```

- [ ] **Step 2: Implement priority logic**

```python
def match(self, user_input: str) -> MatchResult:
    """匹配用户输入到场景（带优先级）"""
    # ... 现有匹配逻辑 ...

    # 如果有多个匹配，选择优先级最高的
    candidates = []
    for scenario_id, config in self.scenarios.items():
        # ... 匹配逻辑 ...
        if confidence > 0:
            candidates.append({
                "scenario_id": scenario_id,
                "confidence": confidence,
                "priority": config.get("priority", 999),
                "matched_keywords": matches
            })

    if not candidates:
        return MatchResult(
            scenario_id="maintenance",
            confidence=1.0,
            matched_keywords=[]
        )

    # 按优先级排序（数字越小优先级越高）
    best_match = min(candidates, key=lambda x: x["priority"])

    return MatchResult(
        scenario_id=best_match["scenario_id"],
        confidence=best_match["confidence"],
        matched_keywords=best_match["matched_keywords"]
    )
```

- [ ] **Step 3: Run test**

Run: `pytest tests/test_scenario_matcher.py::test_scenario_priority -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add .claude/ultimate-team/core/scenario_matcher.py tests/test_scenario_matcher.py
git commit -m "feat: add scenario priority matching"
```

---

### Task 3: 创建场景配置文件

**Files:**
- Create: `.claude/ultimate-team/scenarios/scenarios.yaml`
- Create: `.claude/ultimate-team/scenarios/__init__.py`
- Create: `tests/test_scenario_config.py`

- [ ] **Step 1: Write config file**

```yaml
# .claude/ultimate-team/scenarios/scenarios.yaml
new_feature:
  name: "新功能开发"
  triggers:
    - 添加
    - 实现
    - 新增功能
  strong_match: false
  priority: 30  # 中等优先级
  agents: [planner, frontend-dev, backend-dev, code-reviewer, qa-tester]
  skills: [brainstorming, writing-plans, test-driven-development, verification]
  closed_loops: [B, E, F]
  estimated_time_simple: "2h"
  estimated_time_medium: "3h"
  estimated_time_complex: "4h"

bug_fix:
  name: "Bug 修复"
  triggers:
    - 修复
    - fix
    - bug
    - 错误
  strong_match: false
  priority: 20  # 高优先级
  agents: [coordinator, developer, code-reviewer]
  skills: [systematic-debugging, test-driven-development, verification]
  closed_loops: [B, E]
  estimated_time_simple: "30min"
  estimated_time_complex: "2h"

refactor:
  name: "代码重构"
  triggers:
    - 重构
    - 优化代码
    - 改善结构
  strong_match: true  # "重构"必须精确匹配
  priority: 40
  agents: [architect, developer, code-reviewer]
  skills: [brainstorming, writing-plans, test-driven-development]
  closed_loops: [B, F]
  estimated_time: "1-3h"

performance_optimization:
  name: "性能优化"
  triggers:
    - 性能
    - 优化速度
    - 提升效率
  strong_match: false
  priority: 50
  agents: [developer, performance-specialist, code-reviewer]
  skills: [systematic-debugging, profiling, verification]
  closed_loops: [B, E]
  estimated_time: "2-6h"

security_review:
  name: "安全审查"
  triggers:
    - 安全
    - 漏洞
    - 安全审查
  strong_match: true
  priority: 10  # 最高优先级
  agents: [security-reviewer, code-reviewer, developer]
  skills: [security-review, security-scan, systematic-debugging]
  closed_loops: [E, F]
  estimated_time: "1-2h"

urgent_release:
  name: "紧急发布"
  triggers:
    - 紧急
    - hotfix
    - 立即发布
  strong_match: false
  priority: 1  # 紧急
  agents: [coordinator, developer, devops]
  skills: [test-driven-development, verification, finishing-branch]
  closed_loops: [B]
  estimated_time: "30min-1h"

maintenance:
  name: "常规维护"
  triggers:
    - 更新
    - 升级
    - 维护
  strong_match: false
  priority: 60  # 低优先级
  agents: [developer, code-reviewer]
  skills: [test-driven-development, code-review]
  closed_loops: [B]
  estimated_time: "30min-1h"

documentation:
  name: "文档更新"
  triggers:
    - 文档
    - 说明
    - 更新文档
  strong_match: true
  priority: 50
  agents: [planner, documentation-specialist]
  skills: [brainstorming, writing-clearly]
  closed_loops: [F]
  estimated_time: "1-2h"
```

- [ ] **Step 2: Write config test**

```python
# tests/test_scenario_config.py
import pytest
import yaml
from ultimate_team.scenarios import load_scenarios

def test_load_scenarios():
    """测试加载场景配置"""
    scenarios = load_scenarios()

    assert "new_feature" in scenarios
    assert scenarios["new_feature"]["priority"] == 30
    assert len(scenarios) == 8
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_scenario_config.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add .claude/ultimate-team/scenarios/ tests/test_scenario_config.py
git commit -m "feat: add scenario configuration with 8 preset scenarios"
```

---

## Chunk 2: 场景路由器

### Task 4: 实现路由决策逻辑

**Files:**
- Create: `.claude/ultimate-team/core/router.py`
- Create: `tests/test_router.py`

- [ ] **Step 1: Write router tests**

```python
# tests/test_router.py
import pytest
from ultimate_team.core.router import ScenarioRouter

def test_route_to_fast_path():
    """测试路由到快速路径"""
    router = ScenarioRouter()

    analysis = router.analyze("添加批量转换功能")
    assert analysis["is_common_scenario"] == True

    path_type, scenario = router.route(analysis)
    assert path_type == "FAST_PATH"
    assert scenario["scenario_id"] == "new_feature"

def test_route_to_smart_path():
    """测试路由到智能路径"""
    router = ScenarioRouter()

    # 复杂场景
    analysis = router.analyze("重构支付系统同时添加新功能并优化性能")
    assert analysis["is_common_scenario"] == False

    path_type, scenario = router.route(analysis)
    assert path_type == "SMART_PATH"
    assert scenario is None
```

- [ ] **Step 2: Implement router**

```python
# .claude/ultimate-team/core/router.py
from .scenario_matcher import ScenarioMatcher

class ScenarioRouter:
    """场景路由器"""

    def __init__(self):
        self.matcher = ScenarioMatcher()

    def analyze(self, user_input: str) -> Dict:
        """分析用户需求"""
        # 使用场景匹配器
        match_result = self.matcher.match(user_input)

        # 分析复杂度
        complexity = self._assess_complexity(user_input)

        return {
            "intent": user_input,
            "scenario_id": match_result.scenario_id,
            "confidence": match_result.confidence,
            "is_common_scenario": match_result.confidence > 0.7,
            "complexity": complexity
        }

    def _assess_complexity(self, user_input: str) -> str:
        """评估复杂度"""
        # 简单规则：字数、特殊词、多任务
        word_count = len(user_input.split())

        # 包含"同时"、"并且"等多任务标志
        multi_task = any(word in user_input for word in ["同时", "并且", "加上"])

        if word_count < 10 and not multi_task:
            return "simple"
        elif word_count > 20 or multi_task:
            return "complex"
        else:
            return "medium"

    def route(self, analysis: Dict) -> Tuple[str, Optional[Dict]]:
        """路由决策"""
        if analysis["is_common_scenario"]:
            # 快速路径
            scenario = self._get_scenario_config(analysis["scenario_id"])
            return "FAST_PATH", scenario
        else:
            # 智能路径
            return "SMART_PATH", None

    def _get_scenario_config(self, scenario_id: str) -> Dict:
        """获取场景配置"""
        from ultimate_team.scenarios import load_scenarios
        scenarios = load_scenarios()
        return scenarios.get(scenario_id)
```

- [ ] **Step 3: Run router tests**

Run: `pytest tests/test_router.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add .claude/ultimate-team/core/router.py tests/test_router.py
git commit -m "feat: implement scenario router with fast/smart path decision"
```

---

## Chunk 3: 主入口和 CLI 接口

### Task 5: 创建主入口

**Files:**
- Create: `.claude/skills/ultimate-team.md`
- Create: `.claude/bin/ultimate-team`

- [ ] **Step 1: Write skill file**

```markdown
---
name: ultimate-team
description: Use when 需要智能团队组建、任务管理、或执行完整的开发工作流。支持 8 种预设场景的快速匹配和复杂场景的 AI 决策。集成 Superpowers 工作流，强制执行 3 个核心闭环（开发、反馈、全流程），提供 Markdown 汇总、CLI 工具和 Git 集成。
---

# Ultimate Team

智能元协调系统 - 整合所有 agents、skills、工作流的完整团队管理工具。

## 使用方法

```bash
ultimate-team [user_request]
```

## 示例

```bash
# 自动场景匹配（快速路径）
ultimate-team 添加批量转换功能

# 复杂场景（智能路径）
ultimate-team 重构支付系统并添加新功能

# 查看任务状态
tasks list

# 查看特定任务
tasks show TASK-001
```

## 工作流程

1. 分析用户需求
2. 匹配到场景（快速路径）或 AI 决策（智能路径）
3. 创建和分配任务
4. 执行闭环工作流
5. 更新任务状态
```

- [ ] **Step 2: Write CLI tool**

```python
#!/usr/bin/env python3
# .claude/bin/ultimate-team
import sys
sys.path.insert(0, ".")
from ultimate_team.core.router import ScenarioRouter
from ultimate_team.task_manager import TaskManager

def main():
    if len(sys.argv) < 2:
        print("Usage: ultimate-team <user_request>")
        sys.exit(1)

    user_request = " ".join(sys.argv[1:])

    # 路由
    router = ScenarioRouter()
    analysis = router.analyze(user_request)
    path_type, scenario = router.route(analysis)

    # 执行
    if path_type == "FAST_PATH":
        print(f"🚀 快速路径: {scenario['name']}")
        # TODO: 执行快速路径
    else:
        print(f"🧠 智能路径: 正在分析...")
        # TODO: 调用 AI 分析器

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Make executable**

Run: `chmod +x .claude/bin/ultimate-team`

- [ ] **Step 4: Test CLI**

Run: `ultimate-team 添加批量转换功能`
Expected: 输出场景匹配结果

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ultimate-team.md .claude/bin/ultimate-team
git commit -m "feat: add ultimate-team CLI interface"
```

---

## Chunk 4: 集成测试

### Task 6: 端到端集成测试

**Files:**
- Create: `tests/integration/test_routing_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/integration/test_routing_integration.py
import pytest
from ultimate_team.core.router import ScenarioRouter

def test_full_routing_flow():
    """测试完整的路由流程"""
    router = ScenarioRouter()

    # 测试简单请求
    analysis1 = router.analyze("修复登录bug")
    assert analysis1["is_common_scenario"] == True

    path1, scenario1 = router.route(analysis1)
    assert path1 == "FAST_PATH"
    assert scenario1["name"] == "Bug 修复"

    # 测试复杂请求
    analysis2 = router.analyze("重构认证系统同时优化数据库性能")
    assert analysis2["is_common_scenario"] == False

    path2, scenario2 = router.route(analysis2)
    assert path2 == "SMART_PATH"
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/integration/test_routing_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_routing_integration.py
git commit -m "test: add integration test for routing flow"
```

---

## 总结

**完成的组件**:
- ✅ 场景匹配器（支持精确匹配和多关键词匹配）
- ✅ 场景优先级排序（8 种预设场景按优先级）
- ✅ 场景配置文件（8 种场景的完整配置）
- ✅ 场景路由器（快速/智能路径决策）
- ✅ CLI 接口（基础命令行工具）
- ✅ 集成测试（端到端流程验证）

**下一步**: 实施 Part 2 - 任务管理系统
