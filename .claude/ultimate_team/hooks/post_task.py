#!/usr/bin/env python3
"""
任务后 Hook

任务完成后执行：
1. 运行测试
2. 代码检查
3. 生成摘要
4. 可选：创建 PR
"""

import sys
import subprocess

def main():
    task_id = sys.argv[1] if len(sys.argv) > 1 else None
    create_pr = sys.argv[2] == "true" if len(sys.argv) > 2 else False

    print("🧪 运行测试...")
    result = subprocess.run(["pytest", "-v"])

    if result.returncode != 0:
        print("❌ 测试失败")
        return 1

    print("📊 代码检查...")
    subprocess.run(["ruff", "check", "."])
    subprocess.run(["mypy", "."])

    # 更新任务摘要
    if task_id:
        print("📝 更新任务摘要...")
        subprocess.run([
            sys.executable, ".claude/bin/tasks", "summary",
            "-o", f".claude/tasks/{task_id}.md"
        ])

    if create_pr:
        print("🔀 创建 Pull Request...")
        # TODO: 实现 PR 创建逻辑

    print("✅ 任务完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
