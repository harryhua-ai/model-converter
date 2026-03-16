#!/bin/bash
# install-global.sh - 安装 ultimate-team skill 到全局

set -e

echo "🚀 安装 Ultimate Team Skill 到全局..."

# ===== 1. 创建必要的全局目录 =====
echo "📁 创建全局目录..."
mkdir -p ~/.claude/skills
mkdir -p ~/.claude/bin
mkdir -p ~/.claude/lib/ultimate_team

# ===== 2. 复制 Skill 文件 =====
echo "📄 复制 skill 文件..."
cp skills/ultimate-team.md ~/.claude/skills/
echo "✅ Skill 文件已复制到 ~/.claude/skills/ultimate-team.md"

# ===== 3. 复制 Python 模块 =====
echo "🐍 复制 Python 模块..."
cp -r ultimate_team/* ~/.claude/lib/ultimate_team/
echo "✅ Python 模块已复制到 ~/.claude/lib/ultimate_team/"

# ===== 4. 创建全局 CLI 工具 =====
echo "🔧 创建全局 CLI 工具..."

# ultimate-team CLI
cat > ~/.claude/bin/ultimate-team << 'EOF'
#!/usr/bin/env python3
"""Ultimate Team 全局 CLI"""
import sys
import os

# 添加全局库路径
sys.path.insert(0, os.path.expanduser("~/.claude/lib"))

from ultimate_team.core.router import ScenarioRouter
from ultimate_team.task_manager import TaskManager

def main():
    if len(sys.argv) < 2:
        print("Usage: ultimate-team <user_request>")
        print("\n示例:")
        print("  ultimate-team 添加批量转换功能")
        print("  ultimate-team 修复转换失败的 bug")
        print("  ultimate-team 重构支付系统并添加新功能")
        sys.exit(1)

    user_request = " ".join(sys.argv[1:])

    # 路由
    router = ScenarioRouter()
    analysis = router.analyze(user_request)
    path_type, scenario = router.route(analysis)

    # 执行
    if path_type == "FAST_PATH":
        print(f"🚀 快速路径: {scenario['name']}")
        print(f"   场景 ID: {scenario['scenario_id']}")
        print(f"   置信度: {analysis['confidence']:.2f}")
        print(f"   复杂度: {analysis['complexity']}")
        print(f"\n   推荐的 Agents: {', '.join(scenario['agents'])}")
        print(f"   推荐的 Skills: {', '.join(scenario['skills'])}")
        print(f"   执行闭环: {', '.join(scenario['closed_loops'])}")
        print(f"   预估时间: {scenario['estimated_time']}")
    else:
        print(f"🧠 智能路径: 正在分析...")
        print(f"   复杂度: {analysis['complexity']}")
        print(f"   需要动态规划和 AI 推理")

if __name__ == "__main__":
    main()
EOF

chmod +x ~/.claude/bin/ultimate-team
echo "✅ ultimate-team CLI 已安装"

# tasks CLI
cat > ~/.claude/bin/tasks << 'EOF'
#!/usr/bin/env python3
"""Tasks 全局 CLI"""
import sys
import argparse
from pathlib import Path

# 添加全局库路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from ultimate_team.task_manager.task import Task
from ultimate_team.task_manager.persistence import TaskPersistence
from ultimate_team.tasks.summary_generator import SummaryGenerator

DEFAULT_TASKS_FILE = Path.home() / ".claude" / "tasks" / "tasks.json"

def cmd_list(args):
    """列出所有任务"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    if not tasks:
        print("没有任务")
        return

    print(f"共 {len(tasks)} 个任务:\n")

    for task in tasks:
        status_icon = {
            0: "⏳",  # PENDING
            1: "🔄",  # IN_PROGRESS
            2: "✅",  # COMPLETED
            3: "❌",  # FAILED
            4: "🚫"   # BLOCKED
        }.get(task.status.value, "❓")

        print(f"{status_icon} {task.task_id}: {task.subject}")
        if task.owner:
            print(f"   负责人: {task.owner}")
        print()

def cmd_show(args):
    """显示任务详情"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    task = next((t for t in tasks if t.task_id == args.task_id), None)

    if not task:
        print(f"错误: 未找到任务 {args.task_id}")
        sys.exit(1)

    print(f"任务 ID: {task.task_id}")
    print(f"主题: {task.subject}")
    print(f"描述: {task.description or '(无)'}")
    print(f"状态: {task.status.name}")
    print(f"优先级: {task.priority.name}")
    print(f"负责人: {task.owner or '(未分配)'}")

    if task.dependencies:
        print(f"依赖: {', '.join(task.dependencies)}")

    if task.error:
        print(f"错误: {task.error}")

    print(f"创建时间: {task.created_at}")
    if task.started_at:
        print(f"开始时间: {task.started_at}")
    if task.completed_at:
        print(f"完成时间: {task.completed_at}")

def cmd_stats(args):
    """显示统计信息"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    generator = SummaryGenerator()
    stats = generator.generate_statistics(tasks)

    print("任务统计:")
    print(f"  总任务数: {stats['total']}")
    print(f"  已完成: {stats['completed']}")
    print(f"  进行中: {stats['in_progress']}")
    print(f"  待处理: {stats['pending']}")
    print(f"  已失败: {stats['failed']}")
    print(f"  已阻塞: {stats['blocked']}")

def cmd_summary(args):
    """生成 Markdown 摘要"""
    persistence = TaskPersistence(args.file)
    tasks = persistence.load()

    generator = SummaryGenerator()

    if args.output:
        generator.save(tasks, args.output)
        print(f"摘要已保存到: {args.output}")
    else:
        summary = generator.generate(tasks)
        print(summary)

def main():
    parser = argparse.ArgumentParser(description="任务管理 CLI 工具")
    parser.add_argument("--file", default=str(DEFAULT_TASKS_FILE), help="任务文件路径")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有任务")

    # show 命令
    show_parser = subparsers.add_parser("show", help="显示任务详情")
    show_parser.add_argument("task_id", help="任务 ID")

    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")

    # summary 命令
    summary_parser = subparsers.add_parser("summary", help="生成摘要")
    summary_parser.add_argument("-o", "--output", help="输出文件路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "list": cmd_list,
        "show": cmd_show,
        "stats": cmd_stats,
        "summary": cmd_summary
    }

    command_func = commands.get(args.command)
    if command_func:
        command_func(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x ~/.claude/bin/tasks
echo "✅ tasks CLI 已安装"

# ===== 5. 创建任务存储目录 =====
mkdir -p ~/.claude/tasks
echo "✅ 任务存储目录已创建: ~/.claude/tasks/"

# ===== 6. 添加到 PATH（可选）=====
if [[ ":$PATH:" != *":$HOME/.claude/bin:"* ]]; then
    echo ""
    echo "⚠️  警告: ~/.claude/bin 未在 PATH 中"
    echo ""
    echo "请运行以下命令添加到 PATH:"
    echo ""
    echo "  echo 'export PATH=\"\$HOME/.claude/bin:\$PATH\"' >> ~/.zshrc"
    echo "  source ~/.zshrc"
    echo ""
    echo "或者临时使用:"
    echo "  export PATH=\"\$HOME/.claude/bin:\$PATH\""
fi

# ===== 7. 验证安装 =====
echo ""
echo "✨ 安装完成！验证安装:"
echo ""

if command -v ultimate-team &> /dev/null; then
    echo "✅ ultimate-team 命令可用"
    ultimate-team --help 2>&1 || true
else
    echo "⚠️  ultimate-team 命令不在 PATH 中"
    echo "   完整路径: ~/.claude/bin/ultimate-team"
fi

echo ""
if command -v tasks &> /dev/null; then
    echo "✅ tasks 命令可用"
    tasks --help 2>&1 || true
else
    echo "⚠️  tasks 命令不在 PATH 中"
    echo "   完整路径: ~/.claude/bin/tasks"
fi

echo ""
echo "🎉 全局安装完成！"
echo ""
echo "使用方法:"
echo "  ultimate-team 添加批量转换功能"
echo "  tasks list"
echo "  tasks show TASK-001"
