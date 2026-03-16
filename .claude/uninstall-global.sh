#!/bin/bash
# uninstall-global.sh - 卸载全局 ultimate-team skill

set -e

echo "🗑️  卸载 Ultimate Team Skill..."

# ===== 1. 删除 CLI 工具 =====
echo "删除 CLI 工具..."
rm -f ~/.claude/bin/ultimate-team
rm -f ~/.claude/bin/tasks
echo "✅ CLI 工具已删除"

# ===== 2. 删除 Python 模块 =====
echo "删除 Python 模块..."
rm -rf ~/.claude/lib/ultimate_team
echo "✅ Python 模块已删除"

# ===== 3. 删除 Skill 文件 =====
echo "删除 skill 文件..."
rm -f ~/.claude/skills/ultimate-team.md
echo "✅ Skill 文件已删除"

# ===== 4. 保留任务数据（询问用户）=====
echo ""
read -p "是否删除任务数据 (~/.claude/tasks/)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.claude/tasks
    echo "✅ 任务数据已删除"
else
    echo "⏭️  保留任务数据"
fi

echo ""
echo "✨ 卸载完成！"
