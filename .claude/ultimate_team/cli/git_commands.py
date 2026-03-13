#!/usr/bin/env python3
"""
Git CLI 命令

提供便捷的 Git 操作命令
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ultimate_team.git_integration import (
    WorktreeManager,
    BranchStrategy,
    BranchType
)

def cmd_create_branch(args):
    """创建分支"""
    strategy = BranchStrategy()

    # 解析分支类型
    try:
        branch_type = BranchType(args.type)
    except ValueError:
        print(f"❌ 无效的分支类型: {args.type}")
        return 1

    # 生成分支名
    branch_name = strategy.create_branch_name(branch_type, args.identifier)

    print(f"🔧 创建分支: {branch_name}")

    # 获取基础分支
    base_branch = args.base or strategy.get_base_branch(branch_type)

    # 创建分支
    import subprocess
    try:
        subprocess.run(
            ["git", "checkout", "-b", branch_name, base_branch],
            check=True
        )
        print(f"✅ 分支创建成功: {branch_name}")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ 创建分支失败: {e}")
        return 1

def cmd_worktree(args):
    """Worktree 操作"""
    manager = WorktreeManager(".")

    if args.action == "create":
        worktree_path = manager.create(args.branch, args.base)

        if worktree_path:
            print(f"✅ Worktree 创建成功: {worktree_path}")
            return 0
        else:
            print("❌ Worktree 创建失败")
            return 1

    elif args.action == "list":
        worktrees = manager.list()

        print(f"📋 Worktree 列表 ({len(worktrees)} 个):")
        for wt in worktrees:
            print(f"  - {wt.branch} @ {wt.path}")

        return 0

    elif args.action == "remove":
        if manager.remove(args.branch):
            print(f"✅ Worktree 移除成功: {args.branch}")
            return 0
        else:
            print("❌ Worktree 移除失败")
            return 1

def main():
    parser = argparse.ArgumentParser(description="Git 工具命令")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # create-branch 命令
    branch_parser = subparsers.add_parser("create-branch", help="创建分支")
    branch_parser.add_argument("type", help="分支类型 (feature/fix/hotfix/task)")
    branch_parser.add_argument("identifier", help="标识符")
    branch_parser.add_argument("--base", help="基础分支")

    # worktree 命令
    worktree_parser = subparsers.add_parser("worktree", help="Worktree 操作")
    worktree_parser.add_argument("action", choices=["create", "list", "remove"], help="操作")
    worktree_parser.add_argument("--branch", help="分支名")
    worktree_parser.add_argument("--base", default="main", help="基础分支")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "create-branch":
        return cmd_create_branch(args)
    elif args.command == "worktree":
        return cmd_worktree(args)

    return 0

# 导出的便捷函数
def git_create_branch(branch_type: str, identifier: str, base: str = None):
    """创建分支（便捷函数）"""
    sys.argv = ["git", "create-branch", branch_type, identifier]
    if base:
        sys.argv.extend(["--base", base])

    return main()

def git_status():
    """显示 Git 状态（便捷函数）"""
    import subprocess
    subprocess.run(["git", "status"])

if __name__ == "__main__":
    sys.exit(main())
