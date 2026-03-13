# Ultimate Team 设计文档

**创建日期**: 2026-03-13
**版本**: 1.0
**作者**: Claude + 用户协作

---

## 1. 概述

### 1.1 目标

创建一个**智能元协调系统**，能够：
- 整合所有可用的 agents、skills、工作流
- 根据实际情况智能选择最佳组合
- 强制执行 3 个核心闭环（开发、反馈、全流程）
- 完全替代现有的 team-create skill

### 1.2 核心价值

- **智能化**: AI 根据项目上下文选择最优资源
- **混合模式**: 80% 常见场景用预设规则（快速），20% 复杂场景用 AI（灵活）
- **闭环保障**: 强制执行 3 个核心闭环，确保质量
- **可视化**: Markdown 汇总 + CLI 工具 + Git 集成
- **可扩展**: 支持所有场景，完全覆盖

---

## 2. 架构设计

### 2.1 整体架构（混合架构）

```
用户输入 → 场景路由器 → 快速路径 / 智能路径 → 资源编排器 → 闭环执行引擎
                ↓
         (80% 预设规则)  (20% AI决策)
```

### 2.2 核心组件

1. **场景路由器 (ScenarioRouter)**
   - 分析用户需求
   - 判断场景类型
   - 路由到合适路径

2. **快速路径 (Fast Path)**
   - 8 种预设场景
   - 预定义最佳组合
   - 直接执行

3. **智能路径 (Smart Path)**
   - AI 实时分析
   - 动态资源编排
   - 处理复杂场景

4. **资源编排器 (ResourceOrchestrator)**
   - Agents 池
   - Skills 池
   - 工作流模板库

5. **闭环执行引擎 (ClosedLoopExecutor)**
   - 开发闭环 (B)
   - 反馈闭环 (E)
   - 全流程闭环 (F)

6. **任务管理系统 (TaskManager)**
   - 任务队列
   - 任务调度
   - 任务依赖
   - 任务持久化

---

### 2.3 核心数据结构定义

#### 2.3.1 Agents 池

```python
class Agent:
    """Agent 定义"""
    def __init__(self, name, agent_type, skills, availability):
        self.name = name  # agent 名称
        self.agent_type = agent_type  # agent 类型
        self.skills = skills  # 可用 skills 列表
        self.availability = availability  # 可用性状态
        self.current_task = None  # 当前执行的任务

class AgentPool:
    """Agent 池管理"""
    def __init__(self):
        # 所有可用 agents
        self.agents = [
            Agent("architect", "architecture-specialist",
                 ["backend-patterns", "frontend-patterns", "api-design"],
                 "available"),
            Agent("planner", "planning-specialist",
                 ["brainstorming", "writing-plans"],
                 "available"),
            Agent("frontend-dev", "frontend-developer",
                 ["test-driven-development", "frontend-patterns", "systematic-debugging"],
                 "available"),
            Agent("backend-dev", "backend-developer",
                 ["test-driven-development", "backend-patterns", "api-design"],
                 "available"),
            # ... 更多 agents
        ]

    def find_available_agents(self, required_skill=None):
        """查找可用的 agents"""
        available = []
        for agent in self.agents:
            if agent.availability == "available":
                if required_skill is None or required_skill in agent.skills:
                    available.append(agent)
        return available

    def mark_agent_busy(self, agent_name, task_id):
        """标记 agent 为忙碌"""
        agent = self.get_agent(agent_name)
        if agent:
            agent.availability = "busy"
            agent.current_task = task_id

    def mark_agent_available(self, agent_name):
        """标记 agent 为可用"""
        agent = self.get_agent(agent_name)
        if agent:
            agent.availability = "available"
            agent.current_task = None
```

#### 2.3.2 Skills 池

```python
class Skill:
    """Skill 定义"""
    def __init__(self, name, category, description):
        self.name = name  # skill 名称
        self.category = category  # 类别：superpowers/everything-claude-code/custom
        self.description = description  # 描述
        self.triggers = []  # 触发条件

class SkillPool:
    """Skill 池管理"""
    def __init__(self):
        # 从各个来源加载 skills
        self.skills = self.load_all_skills()

    def load_all_skills(self):
        """加载所有可用的 skills"""
        skills = []

        # 1. Superpowers skills
        superpowers_skills = [
            Skill("brainstorming", "superpowers",
                 "创造性工作前必须使用"),
            Skill("writing-plans", "superpowers",
                 "编写实施计划"),
            Skill("test-driven-development", "superpowers",
                 "TDD 工作流"),
            Skill("systematic-debugging", "superpowers",
                 "系统化调试"),
            Skill("verification-before-completion", "superpowers",
                 "完成前验证"),
            # ... 更多
        ]
        skills.extend(superpowers_skills)

        # 2. Everything Claude Code skills
        ecc_skills = [
            Skill("code-review", "everything-claude-code",
                 "代码质量审查"),
            Skill("python-review", "everything-claude-code",
                 "Python 代码审查"),
            Skill("e2e", "everything-claude-code",
                 "E2E 测试"),
            # ... 更多
        ]
        skills.extend(ecc_skills)

        # 3. 自定义 skills
        custom_skills = self.load_custom_skills()
        skills.extend(custom_skills)

        return skills

    def find_skills_by_category(self, category):
        """按类别查找 skills"""
        return [s for s in self.skills if s.category == category]

    def find_skills_by_trigger(self, user_input):
        """按触发条件查找 skills"""
        return [s for s in self.skills if any(trigger in user_input for trigger in s.triggers)]
```

#### 2.3.3 工作流模板库

```python
class WorkflowTemplate:
    """工作流模板"""
    def __init__(self, name, stages, required_skills, quality_gates):
        self.name = name  # 工作流名称
        self.stages = stages  # 阶段列表
        self.required_skills = required_skills  # 需要的 skills
        self.quality_gates = quality_gates  # 质量关卡

class WorkflowLibrary:
    """工作流模板库"""
    def __init__(self):
        self.workflows = {
            "feature-dev": WorkflowTemplate(
                name="feature-dev",
                stages=["requirements", "design", "plan", "develop", "integrate", "test", "review"],
                required_skills=["brainstorming", "writing-plans", "test-driven-development"],
                quality_gates=["user_approval", "architecture_review", "test_coverage", "code_review"]
            ),
            "bugfix": WorkflowTemplate(
                name="bugfix",
                stages=["detect", "analyze", "fix", "verify"],
                required_skills=["systematic-debugging", "test-driven-development"],
                quality_gates=["root_cause_found", "fix_verified", "regression_test_passed"]
            ),
            # ... 更多工作流
        }

    def get_workflow(self, name):
        """获取工作流模板"""
        return self.workflows.get(name)

    def register_workflow(self, workflow):
        """注册新的工作流模板"""
        self.workflows[workflow.name] = workflow
```

---

## 3. 预设场景定义

### 3.1 8 种常见场景

| 场景 ID | 名称 | 触发词 | 匹配规则 | Agents | Skills | 闭环 | 预计时间 |
|---------|------|--------|---------|--------|--------|------|----------|
| new_feature | 新功能开发 | 添加、实现、新增功能 | 优先级匹配多个关键词 → 选择此场景 | planner, frontend-dev, backend-dev, code-reviewer, qa-tester | brainstorming, writing-plans, tdd, verification | B, E, F | 简单 2h, 中等 3h, 复杂 4h |
| bug_fix | Bug 修复 | 修复、fix、bug、错误 | 包含"错误"、"问题"等 → 优先匹配此场景 | coordinator, developer, code-reviewer | systematic-debugging, tdd, verification | B, E | 简单 30min, 复杂 2h |
| refactor | 代码重构 | 重构、优化代码、改善结构 | "重构"强匹配，其他弱匹配 | architect, developer, code-reviewer | brainstorming, writing-plans, tdd | B, F | 1-3h |
| performance_optimization | 性能优化 | 性能、优化速度、提升效率 | 包含"性能"、"速度"、"效率" | developer, performance-specialist, code-reviewer | systematic-debugging, profiling, verification | B, E | 2-6h |
| security_review | 安全审查 | 安全、漏洞、安全审查 | "安全"强匹配 | security-reviewer, code-reviewer, developer | security-review, security-scan, systematic-debugging | E, F | 1-2h |
| urgent_release | 紧急发布 | 紧急、hotfix、立即发布 | 最高优先级 | coordinator, developer, devops | tdd, verification, finishing-branch | B | 30min-1h |
| maintenance | 常规维护 | 更新、升级、维护 | 默认场景（无其他匹配） | developer, code-reviewer | tdd, code-review | B | 30min-1h |
| documentation | 文档更新 | 文档、说明、更新文档 | "文档"强匹配 | planner, documentation-specialist | brainstorming, writing-clearly | F | 1-2h |

**场景匹配规则**:
1. **优先级排序**: urgent_release > security_review > bug_fix > new_feature > performance_optimization > refactor > documentation > maintenance
2. **关键词匹配**:
   - 强匹配: 场景名称关键词完全匹配（如"紧急" → urgent_release）
   - 弱匹配: 触发词包含在用户输入中
3. **多场景冲突**: 选择优先级最高的场景
4. **无匹配**: 默认为 maintenance 场景

---

## 4. 闭环设计

### 4.1 核心闭环 1：开发闭环 (B)

```
RED (测试先行) → GREEN (实现代码) → IMPROVE (重构) → REVIEW (审查)
    ↓              ↓              ↓              ↓
  测试必须失败    测试必须通过    代码质量提升    审查必须通过
```

**质量关卡**:
- ☑ RED: 测试失败（证明测试有效）
- ☑ GREEN: 测试通过（证明实现正确）
- ☑ IMPROVE: 代码质量提升
- ☑ REVIEW: 代码审查通过

**检查标准**:
```python
def verify_development_loop(task):
    """验证开发闭环"""
    # RED 阶段
    assert task.test_results["red"]["status"] == "FAILED", "测试必须失败"

    # GREEN 阶段
    assert task.test_results["green"]["status"] == "PASSED", "测试必须通过"
    assert task.test_coverage >= 0.8, "测试覆盖率必须 >= 80%"

    # IMPROVE 阶段
    assert task.code_quality_score > task.original_code_quality_score, "代码质量必须提升"
    # 使用 ruff/mypy 验证
    subprocess.run(["ruff", "check", task.source_files])
    subprocess.run(["mypy", task.source_files])

    # REVIEW 阶段
    assert task.code_review["status"] == "APPROVED", "代码审查必须通过"
    assert task.code_review["critical_issues"] == 0, "无 CRITICAL 问题"
    assert task.code_review["high_issues"] == 0, "无 HIGH 问题"
```

**失败处理**: 修复后重试

### 4.2 核心闭环 2：反馈闭环 (E)

```
DETECT (发现) → ANALYZE (分析) → FIX (修复) → VERIFY (验证)
    ↓             ↓             ↓            ↓
  问题明确记录   找到根本原因   实施修复      确认且无副作用
```

**触发条件**: 测试失败、代码审查问题、运行时错误、性能问题、用户反馈

**失败处理**: 失败后回到 ANALYZE 重新分析

### 4.3 核心闭环 3：全流程闭环 (F)

```
1. REQUIREMENTS → 2. DESIGN → 3. PLAN → 4. DEVELOP → 5. INTEGRATE
    ↓                ↓            ↓           ↓              ↓
  需求文档完成     架构设计合理   计划详细     开发完成       集成成功

6. TEST → 7. REVIEW → 8. DEPLOY → 9. VERIFY
    ↓           ↓            ↓            ↓
  测试通过     审查通过      部署完成     验证通过
```

**9 个质量关卡**:
1. 需求文档完成且用户批准
2. 架构设计合理且技术选型确认
3. 实施计划详细且任务分解合理
4. 开发完成且测试覆盖率 >= 80%
5. 集成联调通过且前后端对接成功
6. 所有测试通过（单元+集成+E2E）
7. 代码审查通过且无 CRITICAL/HIGH 问题
8. 部署配置完成且环境就绪
9. 最终验证通过且文档齐全

**检查标准**:
```python
def verify_full_process_loop(task):
    """验证全流程闭环"""
    # 1. 需求文档
    assert "requirements_doc" in task.deliverables, "需求文档必须存在"
    assert task.user_approval["requirements"] == True, "用户必须批准需求"

    # 2. 架构设计
    assert "architecture_doc" in task.deliverables, "架构文档必须存在"
    assert task.tech_stack_selection is not None, "技术选型必须确认"

    # 3. 实施计划
    assert task.plan_tasks_count >= 3, "任务必须分解（至少3个）"
    assert all(t["estimated_time"] for t in task.plan_tasks), "每个任务必须有时间估算"

    # 4. 开发完成
    assert task.status == "DEVELOPED", "开发必须完成"
    assert task.test_coverage >= 0.8, "测试覆盖率必须 >= 80%"

    # 5. 集成联调
    assert task.integration_test["status"] == "PASSED", "集成测试必须通过"

    # 6. 测试验证
    assert task.unit_tests["status"] == "PASSED", "单元测试必须通过"
    assert task.integration_tests["status"] == "PASSED", "集成测试必须通过"
    assert task.e2e_tests["status"] == "PASSED", "E2E 测试必须通过"

    # 7. 代码审查
    assert task.code_review["status"] == "APPROVED", "代码审查必须通过"
    assert task.code_review["critical_issues"] == 0, "无 CRITICAL 问题"
    assert task.code_review["high_issues"] == 0, "无 HIGH 问题"

    # 8. 部署配置
    assert task.deployment_config["status"] == "READY", "部署配置必须完成"
    assert task.deployment_env["health_check"] == "OK", "环境必须就绪"

    # 9. 最终验证
    assert task.final_verification["status"] == "PASSED", "最终验证必须通过"
    assert all(doc["exists"] for doc in task.documentation.values()), "所有文档必须齐全"
```

**失败处理**: 停止并回滚到上一个成功阶段

---

## 5. 任务管理系统

### 5.1 任务数据模型

```python
Task {
  task_id: str
  title: str
  description: str
  status: PENDING | ASSIGNED | IN_PROGRESS | BLOCKED | COMPLETED | FAILED | CANCELLED | RETRY
  priority: CRITICAL | HIGH | MEDIUM | LOW | DEFERRED

  # 分配
  assigned_to: str  # agent 名称
  assignee_type: str  # agent | human

  # 内容
  skill_required: str
  workflow: str
  stage: str

  # 关系
  depends_on: List[str]
  blocks: List[str]

  # 执行
  start_time: datetime
  end_time: datetime
  duration: timedelta
  attempts: int
  max_attempts: int

  # 结果
  result: dict
  error: Exception
  output_files: List[str]

  # 元数据
  metadata: {
    scenario: str
    closed_loop: List[str]
    quality_gates: List[str]
    rollback_point: str
  }
}
```

### 5.2 任务文件结构

```
.claude/tasks/
├── active/
│   ├── TASK-001.json
│   ├── TASK-002.json
│   └── ...
├── completed/
│   ├── TASK-003.json
│   └── ...
├── failed/
│   └── TASK-004.json
├── summary.md           # ← 可读的 Markdown 汇总
├── stats.json           # 统计数据
└── timeline.md          # 时间线视图
```

### 5.3 任务调度算法

```python
def schedule_tasks():
    """任务调度算法"""
    while True:
        # 1. 从优先级队列获取任务
        task = task_queue.dequeue()
        if not task:
            break

        # 2. 查找可用的 agent
        agent = find_available_agent(task)
        if not agent:
            # 没有可用 agent，重新入队
            task_queue.enqueue(task)
            break

        # 3. 分配任务
        assign_task(task, agent)

        # 4. 查找独立任务（可并行）
        independent_tasks = find_independent_tasks(task)
        if independent_tasks:
            # 使用 dispatching-parallel-agents skill
            execute_parallel(task, independent_tasks)
```

**任务独立性判断规则**:
```python
def find_independent_tasks(self, task):
    """查找与当前任务独立的任务（可并行执行）"""
    independent = []

    for other_task in self.task_queue.task_registry.values():
        if other_task.status != "PENDING":
            continue

        # 检查依赖关系
        if (other_task.task_id in task.depends_on or
            task.task_id in other_task.depends_on):
            continue

        # 检查共享状态（文件、资源）
        if self.has_shared_state(task, other_task):
            continue

        # 检查技能冲突（同一 agent 能力冲突）
        if self.has_skill_conflict(task, other_task):
            continue

        independent.append(other_task)

    return independent
```

**共享状态检查**:
- 文件共享: 两个任务操作同一文件
- 资源共享: 两个任务使用同一资源（如数据库连接）
- Agent 共享: 两个任务需要同一 agent 的专有能力

**并行执行控制**:
```python
def execute_parallel(self, main_task, independent_tasks):
    """并行执行独立任务"""
    parallel_agents = []

    for task in independent_tasks:
        agent = self.find_available_agent(task)
        if agent:
            parallel_agents.append((agent, task))

    # 限制并行数量（避免资源耗尽）
    max_parallel = min(len(parallel_agents), 3)
    parallel_agents = parallel_agents[:max_parallel]

    # 并行启动并收集结果
    results = []
    for agent, task in parallel_agents:
        try:
            result = self.execute_with_timeout(agent, task, timeout=timedelta(hours=2))
            results.append((task, result))
        except TimeoutError:
            # 超时任务转为串行
            self.task_queue.enqueue(task)

    # 检查失败任务
    failed_tasks = [t for t, r in results if r is None]
    for failed_task in failed_tasks:
        if failed_task.attempts < failed_task.max_attempts:
            # 重试
            failed_task.status = "RETRY"
            failed_task.attempts += 1
            self.task_queue.enqueue(failed_task)
```

**失败回滚策略**:
- 单个任务失败: 不影响其他并行任务
- 所有任务失败: 回滚到串行模式
- 超时处理: 任务重新入队，降低优先级

---

## 6. 可视化和持久化

### 6.1 Markdown 汇总（`.claude/tasks/summary.md`）

**内容结构**:
- 📊 统计信息
- 🔄 活跃任务（详细）
- ✅ 已完成任务（最近 5 个）
- ❌ 失败任务
- 📈 本周统计

**更新频率**: 每次任务状态变更时自动更新

### 6.2 CLI 工具（`tasks` 命令）

**可用命令**:
```bash
tasks list              # 列出所有任务
tasks show TASK-001     # 显示任务详情
tasks progress TASK-001 # 显示任务进度
tasks stats             # 显示统计信息
tasks watch             # 实时监控（5秒刷新）
```

### 6.3 Git 集成

**功能**:
1. **Worktree 创建**: 为每个任务创建隔离的 git worktree
2. **自动提交**: 提交时自动更新任务状态
3. **分支合并**: 任务完成后自动合并到主分支
4. **Tag 创建**: 已完成任务创建 Git tag

**详细实现**:

**1. Git Hook 自动化**:
```bash
# .git/hooks/post-commit
#!/bin/bash
COMMIT_MSG=$(git log -1 --pretty=%B)
TASK_ID=$(echo "$COMMIT_MSG" | grep "Task ID:" | sed 's/Task ID: //')

if [ -n "$TASK_ID" ]; then
  python -c "
import sys
sys.path.insert(0, '.claude/bin')
from tasks_updater import update_task_from_commit
update_task_from_commit('$TASK_ID', 'COMMITTED')
"
fi
```

**2. 任务完成判断标准**:
```python
def is_task_complete(task):
    """判断任务是否完成"""
    # 1. 所有子任务完成
    if task.get('subtasks'):
        if not all(st.get('done', False) for st in task['subtasks']):
            return False

    # 2. 所有质量关卡通过
    if task.get('quality_gates'):
        if not all(gate.get('passed', False) for gate in task['quality_gates']):
            return False

    # 3. 用户确认（可选）
    if task.get('require_user_confirmation'):
        return prompt_user_confirmation(task['task_id'])

    return True
```

**3. 合并失败处理**:
```python
def merge_with_fallback(task):
    """尝试合并，失败时降级"""
    branch_name = task.get('branch_name')

    try:
        subprocess.run([
            "git", "merge", "--no-ff", branch_name
        ], check=True, capture_output=True)
        return True

    except subprocess.CalledProcessError:
        # 合并冲突
        task.status = "MANUAL_INTERVENTION_REQUIRED"
        task.merge_conflict = True
        save_task(task)
        create_merge_instructions(task)
        return False
```

**4. Worktree 创建失败处理**:
```python
def create_task_worktree(task):
    """为任务创建隔离的 git worktree"""
    try:
        subprocess.run([
            "git", "worktree", "add",
            "-b", branch_name,
            worktree_path
        ], check=True, capture_output=True)
        return worktree_path

    except subprocess.CalledProcessError as e:
        if "already exists" in str(e):
            # 复用已存在的 worktree
            return get_existing_worktree(branch_name)
        else:
            # 降级到主分支工作
            click.echo("⚠️  无法创建 worktree，将在主分支工作")
            return None
```

**工作流**:
```bash
ultimate-team 添加功能
  ↓
创建 task worktree
  ↓
在 worktree 中开发
  ↓
git commit（自动更新任务状态）
  ↓
任务完成（自动合并、删除 worktree）
```

---

## 7. 错误处理和恢复

### 7.1 错误类型和策略

| 错误类型 | 严重程度 | 策略 | 具体实现 | 最大重试 |
|---------|---------|------|----------|----------|
| QualityGateError | HIGH | RETRY | 1. 记录失败关卡<br>2. 修复问题<br>3. 重新验证关卡 | 3 |
| TestFailureError | MEDIUM | DEBUG_AND_FIX | 1. 使用 systematic-debugging skill<br>2. 定位根因<br>3. 修复并添加测试<br>4. 超时: 30分钟 | 5 |
| CodeReviewError | MEDIUM | FIX_AND_RESUBMIT | 1. 使用 receiving-code-review skill<br>2. 根据反馈修复<br>3. 重新提交审查 | 3 |
| CriticalError | CRITICAL | ROLLBACK | 1. 停止执行<br>2. 回滚到上一个保存点<br>3. 通知用户<br>4. 创建 Bug 任务 | 0 |
| AgentError | MEDIUM | REPLACE_AGENT | 1. 标记当前 agent 不可用<br>2. 查找替代 agent（按技能匹配）<br>3. 重新分配任务 | 2 |
| SkillError | LOW | SKIP_OR_ALTERNATIVE | 1. 跳过当前 skill<br>2. 使用替代 skill（从预定义映射）<br>3. 记录警告 | 1 |

**错误处理时间限制**:
- DEBUG_AND_FIX: 单次调试不超过 30 分钟
- REPLACE_AGENT: 查找替代 agent 不超过 5 分钟
- 整体错误处理不超过 1 小时

**替代 Skill 映射**:
```python
ALTERNATIVE_SKILLS = {
    "test-driven-development": ["tdd-workflow"],
    "systematic-debugging": ["debugging"],
    "brainstorming": ["planning"],
    "writing-plans": ["blueprint"]
}
```

### 7.2 状态恢复

**保存点机制**:
- 每个阶段完成后保存状态
- 失败时回滚到上一个保存点
- 支持断点续传

**状态文件格式**:
```json
{
  "stage": "DEVELOP",
  "timestamp": "2026-03-13T10:00:00",
  "data": {...},
  "checksum": "abc123"
}
```

---

## 8. 性能考虑

### 8.1 优化策略

1. **快速路径缓存**: 预设场景的结果可缓存
2. **并行执行**: 独立任务并行处理
3. **延迟加载**: Agents 和 Skills 按需加载
4. **增量更新**: 只更新变更的任务文件

### 8.2 可扩展性

1. **水平扩展**: 支持多个 agent 并行工作
2. **垂直扩展**: 支持添加新的 agents、skills、工作流
3. **场景扩展**: 轻松添加新的预设场景

---

## 9. 安全考虑

### 9.1 权限控制

**任务分配权限**:
```python
class PermissionManager:
    """权限管理器"""
    PERMISSIONS = {
        "assign_task": ["admin", "team_lead"],
        "execute_task": ["agent", "human"],
        "rollback_task": ["admin", "system"],
        "delete_task": ["admin", "task_owner"]
    }

    def check_permission(self, user, action, task=None):
        """检查权限"""
        required_role = self.PERMISSIONS.get(action)
        if user.role not in required_role:
            raise PermissionError(f"用户 {user} 无权限执行 {action}")

        # 任务所有者可以删除自己的任务
        if action == "delete_task" and task and task.owner == user:
            return True

        return True
```

**任务所有权**:
- 每个任务有明确的所有者（创建者）
- 所有者可以删除、修改自己的任务
- Team Lead 可以管理所有任务

### 9.2 敏感数据过滤

**敏感数据定义**:
- API 密钥、Token、密码
- 个人身份信息（PII）
- 商业机密数据
- 数据库连接字符串

**自动过滤机制**:
```python
class SensitiveDataFilter:
    """敏感数据过滤器"""
    SENSITIVE_PATTERNS = [
        r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"token\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
    ]

    def filter_task_data(self, task):
        """过滤任务数据中的敏感信息"""
        # 过滤描述
        task.description = self.redact(task.description)

        # 过滤错误信息
        if task.error:
            task.error = self.redact(str(task.error))

        # 过滤输出文件路径
        task.output_files = [
            self.sanitize_path(f) for f in task.output_files
        ]

        return task

    def redact(self, text):
        """脱敏处理"""
        for pattern in self.SENSITIVE_PATTERNS:
            text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
        return text

    def sanitize_path(self, path):
        """清理文件路径中的敏感信息"""
        # 移除用户名、密码等
        path = re.sub(r'://[^/]+:[^@]+@', '://***:***@', path)
        return path
```

### 9.3 审计日志

**日志格式**:
```json
{
  "timestamp": "2026-03-13T10:00:00Z",
  "user": "user_id",
  "action": "create_task",
  "task_id": "TASK-001",
  "details": {...},
  "ip_address": "127.0.0.1",
  "result": "success"
}
```

**保留策略**:
- 正常日志：保留 90 天
- 安全事件日志：保留 365 天
- 失败任务日志：永久保留

### 9.4 回滚安全

**回滚验证**:
```python
def safe_rollback(task, target_stage):
    """安全回滚"""
    # 1. 验证回滚目标
    if not is_valid_rollback_point(task, target_stage):
        raise RollbackError(f"阶段 {target_stage} 不是有效的回滚点")

    # 2. 备份当前状态
    backup = create_backup(task)

    # 3. 执行回滚
    try:
        rollback_to_stage(task, target_stage)
    except Exception as e:
        # 回滚失败，恢复备份
        restore_from_backup(task, backup)
        raise RollbackError(f"回滚失败: {e}")

    # 4. 验证回滚结果
    verify_rollback_integrity(task)
```

---

## 10. 实施计划

### 10.1 第一阶段：核心功能（预计 1-2 周）

- [ ] 场景路由器（2 天）
  - 输入：用户需求 + 项目上下文
  - 输出：场景类型 + 路径决策
  - 验证：能正确匹配 8 种场景

- [ ] 快速路径（8 种场景）（3 天）
  - 输出：8 种场景的预设配置
  - 验证：每种场景可独立执行

- [ ] 任务管理系统（3 天）
  - 输出：任务队列、调度器、持久化
  - 验证：可以创建和追踪任务

- [ ] Markdown 汇总生成器（1 天）
  - 输出：自动生成 `.claude/tasks/summary.md`
  - 验证：汇总文件格式正确

- [ ] 基础 CLI 工具（2 天）
  - 输出：`tasks` 命令
  - 验证：所有子命令可用

**里程碑**: 能够完成简单的任务创建和追踪

### 10.2 第二阶段：高级功能（预计 1-2 周）

- [ ] 智能路径（AI 决策）（4 天）
  - 输出：AI 场景分析和动态编排
  - 验证：能处理复杂场景

- [ ] 闭环执行引擎（4 天）
  - 输出：3 个核心闭环的强制执行
  - 验证：所有关卡能正确验证

- [ ] 错误处理和恢复（3 天）
  - 输出：完整的错误处理策略
  - 验证：所有错误类型能正确处理

- [ ] Git 集成（3 天）
  - 输出：worktree、hooks、自动合并
  - 验证：Git 集成工作流顺畅

**里程碑**: 能够处理完整的开发流程

### 10.3 第三阶段：优化和扩展（预计 1 周）

- [ ] 性能优化（2 天）
  - 输出：缓存、并行处理优化
  - 验证：响应时间 < 2 秒

- [ ] 并行执行优化（2 天）
  - 输出：智能并行任务调度
  - 验证：能并行执行独立任务

- [ ] 新场景添加（1 天）
  - 输出：场景扩展机制
  - 验证：可以添加新场景

- [ ] 文档完善（2 天）
  - 输出：完整的用户文档和 API 文档
  - 验证：文档清晰易懂

**里程碑**: 系统稳定可用，文档完整

---

## 11. 成功标准

### 11.1 功能标准

- ✅ 8 种预设场景全部可用
- ✅ 智能路径能处理复杂场景
- ✅ 3 个核心闭环强制执行
- ✅ 任务管理系统完整可用
- ✅ Markdown 汇总自动生成
- ✅ CLI 工具功能完整
- ✅ Git 集成工作流顺畅

### 11.2 质量标准

- ✅ 所有闭环有明确的质量关卡
- ✅ 错误处理覆盖所有关键路径
- ✅ 任务状态 100% 可追踪
- ✅ 文档完整且准确

### 11.3 用户体验标准

- ✅ 一键启动（无需手动配置）
- ✅ 实时反馈（进度可见）
- ✅ 错误信息清晰
- ✅ 恢复机制可靠

---

## 12. 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| AI 决策不稳定 | 高 | 中 | 保留快速路径作为后备 |
| 任务调度冲突 | 中 | 中 | 依赖管理 + 优先级队列 |
| 性能瓶颈 | 中 | 低 | 并行处理 + 缓存 |
| 用户不接受 | 高 | 低 | 渐进式发布，收集反馈 |

---

## 13. 后续优化方向

1. **机器学习优化**: 根据历史数据优化决策
2. **自动场景识别**: 自动发现新的常见场景
3. **跨项目学习**: 从多个项目中学习最佳实践
4. **自然语言接口**: 支持更自然的交互方式
5. **可视化界面**: Web UI 或 GUI

---

**文档状态**: ✅ 已完成
**下一步**: 规范审查循环