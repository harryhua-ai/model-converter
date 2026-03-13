# tests/test_worktree_manager.py
import pytest
import tempfile
import shutil
from pathlib import Path
from ultimate_team.git_integration.worktree_manager import WorktreeManager

@pytest.fixture
def temp_repo():
    """创建临时仓库"""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)

    # 初始化 Git 仓库
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, capture_output=True)

    # 创建初始提交
    (repo_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)

    yield repo_path

    # 清理
    shutil.rmtree(temp_dir)

def test_create_worktree(temp_repo):
    """测试创建 worktree"""
    manager = WorktreeManager(str(temp_repo))

    worktree_path = manager.create("feature/test-feature", "main")

    assert worktree_path is not None
    assert Path(worktree_path).exists()

    # 验证 worktree 目录
    assert (Path(worktree_path) / ".git").exists()

def test_list_worktrees(temp_repo):
    """测试列出 worktree"""
    manager = WorktreeManager(str(temp_repo))

    # 创建两个 worktree
    manager.create("feature/feat1", "main")
    manager.create("feature/feat2", "main")

    worktrees = manager.list()

    assert len(worktrees) == 3  # main + 2 worktrees

def test_remove_worktree(temp_repo):
    """测试移除 worktree"""
    manager = WorktreeManager(str(temp_repo))

    worktree_path = manager.create("feature/temp", "main")

    # 移除 worktree
    result = manager.remove("feature/temp")

    assert result == True
    assert not Path(worktree_path).exists()
