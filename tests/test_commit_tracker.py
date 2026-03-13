# tests/test_commit_tracker.py
import pytest
import tempfile
import subprocess
from pathlib import Path
from ultimate_team.git_integration.commit_tracker import CommitTracker

@pytest.fixture
def temp_repo():
    """创建临时仓库"""
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

    import shutil
    shutil.rmtree(temp_dir)

def test_track_commits(temp_repo):
    """测试追踪提交"""
    tracker = CommitTracker(str(temp_repo))

    # 创建一些提交
    for i in range(3):
        (temp_repo / f"file{i}.txt").write_text(f"Content {i}")
        subprocess.run(["git", "add", "."], cwd=temp_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Commit {i}"], cwd=temp_repo, capture_output=True)

    commits = tracker.get_recent_commits(limit=5)

    assert len(commits) == 4  # 包括初始提交

def test_get_commit_stats(temp_repo):
    """测试获取提交统计"""
    tracker = CommitTracker(str(temp_repo))

    stats = tracker.get_commit_stats()

    assert "total_commits" in stats
    assert "authors" in stats
    assert stats["total_commits"] >= 1
