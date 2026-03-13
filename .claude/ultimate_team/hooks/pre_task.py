#!/usr/bin/env python3
"""
任务前 Hook

在开始任务前执行：
1. 检查 Git 状态是否干净
2. 创建或切换到任务分支
3. 可选：创建 worktree
"""

import sys
import subprocess
from pathlib import Path

def main():
    task_id = sys.argv[1] if len(sys.argv) > 1 else None
    create_worktree = sys.argv[2] == "true" if len(sys.argv) > 2 else False

    # 检查 Git 状态
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        print("⚠️  工作区不干净，请先提交或暂存更改")
        return 1

    # 创建任务分支
    branch_name = f"task/{task_id}" if task_id else "task/new"

    if create_worktree:
        print(f"🔧 创建 worktree: {branch_name}")
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, f"../worktree-{branch_name}"],
            check=True
        )
    else:
        # 检查分支是否存在
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            capture_output=True
        )

        if result.returncode != 0:
            print(f"🔧 创建分支: {branch_name}")
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True
            )
        else:
            print(f"🔧 切换到分支: {branch_name}")
            subprocess.run(["git", "checkout", branch_name], check=True)

    print(f"✅ 任务环境准备完成: {branch_name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
