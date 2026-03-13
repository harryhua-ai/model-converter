# tests/test_git_commands.py
import pytest
import subprocess
from pathlib import Path

def test_git_create_branch():
    """测试创建分支命令"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / ".claude" / "ultimate_team" / "cli" / "git_commands.py"

    # 测试帮助信息
    result = subprocess.run(
        ["python3", str(script_path), "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Git 工具命令" in result.stdout

def test_git_worktree_list():
    """测试 worktree list 命令"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / ".claude" / "ultimate_team" / "cli" / "git_commands.py"

    result = subprocess.run(
        ["python3", str(script_path), "worktree", "list"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Worktree 列表" in result.stdout
