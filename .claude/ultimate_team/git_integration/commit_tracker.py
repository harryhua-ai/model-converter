# .claude/ultimate_team/git_integration/commit_tracker.py
import subprocess
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CommitInfo:
    """提交信息"""
    hash: str
    author: str
    email: str
    date: datetime
    message: str
    files_changed: int = 0

class CommitTracker:
    """提交追踪器"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def get_recent_commits(self, limit: int = 10) -> List[CommitInfo]:
        """获取最近的提交"""
        try:
            result = subprocess.run(
                [
                    "git", "log",
                    f"--max-count={limit}",
                    "--pretty=format:%H|%an|%ae|%ai|%s",
                    "--numstat"
                ],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )

            lines = result.stdout.splitlines()
            commits = []
            current_commit = None

            for line in lines:
                if "|" in line:
                    # 提交信息行
                    if current_commit:
                        commits.append(current_commit)

                    parts = line.split("|")
                    current_commit = CommitInfo(
                        hash=parts[0],
                        author=parts[1],
                        email=parts[2],
                        date=datetime.fromisoformat(parts[3]),
                        message=parts[4]
                    )
                elif current_commit and line.strip():
                    # 文件变更行
                    current_commit.files_changed += 1

            if current_commit:
                commits.append(current_commit)

            return commits

        except subprocess.CalledProcessError:
            return []

    def get_commit_stats(self) -> Dict[str, any]:
        """获取提交统计"""
        try:
            # 总提交数
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )
            total_commits = int(result.stdout.strip())

            # 作者统计
            result = subprocess.run(
                ["git", "shortlog", "-sn", "--all"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )

            authors = []
            for line in result.stdout.splitlines():
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    authors.append({
                        "commits": int(parts[0]),
                        "name": parts[1]
                    })

            return {
                "total_commits": total_commits,
                "authors": authors
            }

        except subprocess.CalledProcessError:
            return {
                "total_commits": 0,
                "authors": []
            }
