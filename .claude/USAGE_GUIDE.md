# Ultimate Team 全局安装指南

## 📦 安装状态

✅ **已成功安装到全局目录**

安装位置：
- **Skill 文件**: `~/.claude/skills/ultimate-team.md`
- **Python 模块**: `~/.claude/lib/ultimate_team/`
- **CLI 工具**:
  - `~/.claude/bin/ultimate-team`
  - `~/.claude/bin/tasks`
- **任务数据**: `~/.claude/tasks/`

---

## 🚀 快速使用

### 1. 场景匹配（智能路由）

```bash
# 快速路径 - 自动匹配预设场景
ultimate-team 添加批量转换功能
ultimate-team 修复转换失败的 bug
ultimate-team 重构支付系统

# 智能路径 - 复杂场景需要 AI 推理
ultimate-team 重构支付系统并添加新功能
```

**输出示例**：
```
🚀 快速路径: 新功能开发
   场景 ID: new_feature
   置信度: 1.00
   复杂度: simple

   推荐的 Agents: planner, architect, tdd-guide
   推荐的 Skills: python-patterns, typescript-patterns, testing
   执行闭环: B, E, F
   预估时间: 2h
```

### 2. 任务管理

```bash
# 列出所有任务
tasks list

# 查看任务详情
tasks show TASK-001

# 查看统计信息
tasks stats

# 生成 Markdown 摘要
tasks summary -o summary.md
```

---

## ⚙️ PATH 配置（可选）

如果想在任意目录直接使用 `ultimate-team` 和 `tasks` 命令，需要添加到 PATH：

### 临时添加（当前终端会话）

```bash
export PATH="$HOME/.claude/bin:$PATH"
```

### 永久添加（推荐）

**Zsh（macOS 默认）**：
```bash
echo 'export PATH="$HOME/.claude/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Bash**：
```bash
echo 'export PATH="$HOME/.claude/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Fish**：
```bash
set -Ua fish_user_paths $HOME/.claude/bin
```

---

## 🎯 支持的场景

| 场景 | 优先级 | 触发词 | 预估时间 |
|------|--------|--------|----------|
| **紧急发布** | 🔴 紧急 | 紧急、hotfix、立即发布 | 30min-1h |
| **安全审查** | 🔴 最高 | 安全、漏洞、安全审查 | 1-2h |
| **Bug 修复** | 🟠 高 | 修复、fix、bug、错误 | 30min |
| **新功能开发** | 🟡 中 | 添加、实现、新增功能 | 2h |
| **性能优化** | 🟡 中 | 性能、优化速度、提升效率 | 2-6h |
| **代码重构** | 🟢 低 | 重构、优化代码、改善结构 | 1-3h |
| **文档更新** | 🟢 低 | 文档、说明、更新文档 | 1-2h |
| **常规维护** | ⚪ 最低 | 更新、升级、维护 | 30min-1h |

---

## 📁 目录结构

```
~/.claude/
├── skills/
│   └── ultimate-team.md          # Skill 定义
├── bin/
│   ├── ultimate-team             # 主 CLI 工具
│   └── tasks                     # 任务管理 CLI
├── lib/
│   └── ultimate_team/            # Python 模块
│       ├── core/                 # 核心路由和匹配
│       ├── scenarios/            # 场景配置
│       ├── task_manager/         # 任务管理
│       ├── loops/                # 闭环工作流
│       ├── quality/              # 质量保证
│       └── git_integration/      # Git 集成
└── tasks/
    └── tasks.json                # 任务数据存储
```

---

## 🔧 高级配置

### 自定义场景

编辑 `~/.claude/lib/ultimate_team/scenarios/scenarios.yaml`：

```yaml
custom_scenario:
  name: 自定义场景
  triggers:
    - 自定义触发词
    - custom trigger
  priority: 25
  strong_match: false
  agents:
    - planner
    - developer
  skills:
    - python-patterns
    - testing
  closed_loops:
    - B
    - E
  estimated_time: "1-2h"
```

### 修改任务存储位置

```bash
# 使用自定义路径
tasks --file /path/to/custom/tasks.json list
```

---

## 🗑️ 卸载

如需卸载全局安装：

```bash
cd /Users/harryhua/Documents/GitHub/agents/best-team
./uninstall-global.sh
```

---

## 📚 相关文档

- **项目源码**: `/Users/harryhua/Documents/GitHub/agents/best-team/`
- **Skill 分析报告**: 查看之前的分析输出
- **场景配置**: `~/.claude/lib/ultimate_team/scenarios/scenarios.yaml`

---

## 🐛 故障排除

### 问题 1: `command not found: ultimate-team`

**解决方案**：
1. 检查 PATH 配置：`echo $PATH | grep .claude/bin`
2. 添加到 PATH（见上文）
3. 或使用完整路径：`~/.claude/bin/ultimate-team`

### 问题 2: `ImportError: No module named 'ultimate_team'`

**解决方案**：
1. 检查 Python 模块是否存在：`ls ~/.claude/lib/ultimate_team/`
2. 重新运行安装脚本：`./install-global.sh`

### 问题 3: `PyYAML 未安装`

**解决方案**：
```bash
pip3 install pyyaml
# 或
pip install pyyaml
```

---

## 💡 最佳实践

1. **在项目根目录使用**: 在项目根目录运行命令，便于 Git 集成
2. **定期清理任务**: 使用 `tasks summary` 查看进度，及时归档已完成任务
3. **自定义场景**: 根据团队需求添加自定义场景到 `scenarios.yaml`
4. **集成到 CI/CD**: 使用 `tasks` CLI 生成报告，集成到自动化流程

---

## 📞 支持

如有问题或建议，请：
1. 查看源码注释
2. 阅读之前的分析报告
3. 联系开发团队

---

**版本**: 1.0.0
**最后更新**: 2026-03-14
