# tests/test_hook_manager.py
import pytest
import tempfile
import shutil
from pathlib import Path
from ultimate_team.git_integration.hook_manager import HookManager

@pytest.fixture
def repo_with_hooks():
    """创建带 hooks 的仓库"""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)

    # 初始化仓库
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)

    yield repo_path

    shutil.rmtree(temp_dir)

def test_install_hook(repo_with_hooks):
    """测试安装 hook"""
    manager = HookManager(str(repo_with_hooks))

    # 创建测试 hook
    hook_script = """#!/bin/bash
echo "Pre-commit hook executed"
exit 0
"""

    result = manager.install("pre-commit", hook_script)

    assert result == True

    # 验证 hook 文件存在
    hook_path = repo_with_hooks / ".git" / "hooks" / "pre-commit"
    assert hook_path.exists()

def test_list_hooks(repo_with_hooks):
    """测试列出 hooks"""
    manager = HookManager(str(repo_with_hooks))

    # 安装两个 hooks
    manager.install("pre-commit", "#!/bin/bash\necho 'pre-commit'\nexit 0")
    manager.install("post-commit", "#!/bin/bash\necho 'post-commit'\nexit 0")

    hooks = manager.list()

    assert "pre-commit" in hooks
    assert "post-commit" in hooks

def test_remove_hook(repo_with_hooks):
    """测试移除 hook"""
    manager = HookManager(str(repo_with_hooks))

    # 安装 hook
    manager.install("pre-commit", "#!/bin/bash\necho 'test'\nexit 0")

    # 移除 hook
    result = manager.remove("pre-commit")

    assert result == True

    hook_path = repo_with_hooks / ".git" / "hooks" / "pre-commit"
    assert not hook_path.exists()
