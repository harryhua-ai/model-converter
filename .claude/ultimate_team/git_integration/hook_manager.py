# .claude/ultimate_team/git_integration/hook_manager.py
import os
import stat
from pathlib import Path
from typing import Dict, List

class HookManager:
    """Git Hook 管理器"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.hooks_dir = self.repo_path / ".git" / "hooks"

    def install(self, hook_name: str, hook_content: str) -> bool:
        """安装 hook"""
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_path = self.hooks_dir / hook_name

        try:
            hook_path.write_text(hook_content)

            # 设置可执行权限
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IEXEC)

            return True

        except Exception as e:
            print(f"安装 hook 失败: {e}")
            return False

    def remove(self, hook_name: str) -> bool:
        """移除 hook"""
        hook_path = self.hooks_dir / hook_name

        if hook_path.exists():
            hook_path.unlink()
            return True

        return False

    def list(self) -> Dict[str, str]:
        """列出所有 hooks"""
        hooks = {}

        if not self.hooks_dir.exists():
            return hooks

        for hook_file in self.hooks_dir.iterdir():
            if hook_file.is_file() and os.access(hook_file, os.X_OK):
                hooks[hook_file.name] = hook_file.read_text()

        return hooks

    def exists(self, hook_name: str) -> bool:
        """检查 hook 是否存在"""
        hook_path = self.hooks_dir / hook_name
        return hook_path.exists() and os.access(hook_path, os.X_OK)
