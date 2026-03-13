# .claude/ultimate-team/git_integration/worktree_manager.py
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

@dataclass
class WorktreeInfo:
    """Worktree 信息"""
    path: str
    branch: str
    commit: str
    is_bare: bool = False

class WorktreeManager:
    """Git Worktree 管理器"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def create(self, branch: str, base_branch: str = "main") -> Optional[str]:
        """创建新的 worktree"""
        worktree_name = branch.replace("/", "-")
        # 在仓库目录内创建 worktree 目录，而不是在父目录
        worktree_path = self.repo_path / f".worktree-{worktree_name}"

        try:
            # 创建 worktree
            subprocess.run(
                ["git", "worktree", "add", "-b", branch, str(worktree_path), base_branch],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )

            return str(worktree_path)

        except subprocess.CalledProcessError as e:
            print(f"创建 worktree 失败: {e.stderr}")
            return None

    def list(self) -> List[WorktreeInfo]:
        """列出所有 worktree"""
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )

            worktrees = []
            current = {}

            for line in result.stdout.splitlines():
                if not line:
                    if current:
                        worktrees.append(WorktreeInfo(
                            path=current.get("worktree", ""),
                            branch=current.get("branch", "").replace("refs/heads/", ""),
                            commit=current.get("HEAD", ""),
                            is_bare=current.get("bare") is not None
                        ))
                        current = {}
                else:
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        current[parts[0]] = parts[1]

            return worktrees

        except subprocess.CalledProcessError:
            return []

    def remove(self, branch_or_path: str) -> bool:
        """移除 worktree（支持分支名或路径）"""
        try:
            # 首先尝试作为路径删除
            result = subprocess.run(
                ["git", "worktree", "remove", branch_or_path],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )
            return True

        except subprocess.CalledProcessError:
            # 如果失败，尝试查找 worktree 路径
            worktrees = self.list()
            for wt in worktrees:
                if wt.branch == branch_or_path:
                    try:
                        subprocess.run(
                            ["git", "worktree", "remove", wt.path],
                            cwd=self.repo_path,
                            capture_output=True,
                            check=True,
                            text=True
                        )
                        return True
                    except subprocess.CalledProcessError:
                        return False
            return False

    def prune(self) -> bool:
        """清理无效的 worktree"""
        try:
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )
            return True

        except subprocess.CalledProcessError:
            return False
