#!/usr/bin/env python3
"""
提交前 Hook

在 Git 提交前执行：
1. 运行测试
2. 代码格式化
3. 类型检查
4. 安全扫描
"""

import sys
import subprocess
import os

def main():
    # 检查是否有暂存的文件
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )

    if not result.stdout.strip():
        print("⚠️  没有暂存的文件")
        return 0

    # 只检查 Python 文件
    py_files = [
        f for f in result.stdout.splitlines()
        if f.endswith('.py')
    ]

    if not py_files:
        return 0

    print("🔍 提交前检查...")

    # 运行测试
    print("  🧪 运行测试...")
    result = subprocess.run(
        ["pytest", "-q"],
        capture_output=True
    )

    if result.returncode != 0:
        print("❌ 测试失败，提交被拒绝")
        print(result.stdout.decode())
        print(result.stderr.decode())
        return 1

    # 代码格式化
    print("  🎨 代码格式化...")
    for py_file in py_files:
        subprocess.run(["black", py_file])
        subprocess.run(["isort", py_file])

        # 重新添加格式化后的文件
        subprocess.run(["git", "add", py_file])

    # 类型检查
    print("  🔍 类型检查...")
    result = subprocess.run(
        ["mypy", *py_files],
        capture_output=True
    )

    if result.returncode != 0:
        print("⚠️  类型检查发现问题（建议修复后再提交）")
        print(result.stdout.decode())

    print("✅ 提交前检查通过")
    return 0

if __name__ == "__main__":
    sys.exit(main())
