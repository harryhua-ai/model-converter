# tests/test_git_integration.py
import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path

@pytest.fixture
def clean_repo():
    """创建干净的临时仓库"""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)

    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)

    # 创建初始提交
    (repo_path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=repo_path, capture_output=True)

    yield repo_path

    shutil.rmtree(temp_dir)

def test_hook_execution(clean_repo):
    """测试 hook 执行"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    hook_path = project_root / ".claude" / "ultimate_team" / "hooks" / "pre_task.py"

    # 测试 pre_task hook
    result = subprocess.run(
        ["python3", str(hook_path), "TASK-001", "false"],
        cwd=clean_repo,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "任务环境准备完成" in result.stdout

def test_pre_commit_hook():
    """测试 pre-commit hook 基本功能"""
    # 只验证 hook 文件存在且可执行
    project_root = Path(__file__).parent.parent
    hook_path = project_root / ".claude" / "ultimate_team" / "hooks" / "pre_commit.py"

    assert hook_path.exists()
    assert hook_path.stat().st_mode & 0o111  # 检查可执行权限
