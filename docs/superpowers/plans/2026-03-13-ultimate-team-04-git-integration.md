# Ultimate Team - Part 4: Git 集成和工具链实施计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 集成 Git 工作流，包括 worktree 管理、自动化 hooks、分支策略和任务追踪

**Architecture:** Git 操作封装层，通过 Python subprocess 调用 Git 命令，集成到任务生命周期，自动管理 worktree 和 hooks

**Tech Stack:** Python 3.11+, subprocess (Git 命令), GitPython (可选), pathlib (路径管理), dataclasses (数据模型)

---

## 文件结构

```
.claude/
├── ultimate-team/
│   ├── git_integration/
│   │   ├── __init__.py
│   │   ├── worktree_manager.py      # Worktree 管理
│   │   ├── hook_manager.py          # Hook 管理
│   │   ├── branch_strategy.py       # 分支策略
│   │   └── commit_tracker.py        # 提交追踪
│   ├── cli/
│   │   ├── __init__.py
│   │   └── git_commands.py          # Git CLI 命令
│   └── hooks/
│       ├── pre_task.py              # 任务前 hook
│       ├── post_task.py             # 任务后 hook
│       └── pre_commit.py            # 提交前 hook
└── tests/
    ├── test_worktree_manager.py
    ├── test_hook_manager.py
    ├── test_branch_strategy.py
    └── test_git_integration.py
```

---

## Chunk 1: Worktree 管理

### Task 1: 实现 Worktree 管理器

**Files:**
- Create: `.claude/ultimate-team/git_integration/worktree_manager.py`
- Create: `tests/test_worktree_manager.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_worktree_manager.py -v`
Expected: FAIL with "WorktreeManager not defined"

- [ ] **Step 3: Write minimal implementation**

```python
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
        worktree_path = self.repo_path.parent / f"worktree-{worktree_name}"

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

    def remove(self, branch: str) -> bool:
        """移除 worktree"""
        try:
            subprocess.run(
                ["git", "worktree", "remove", branch],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
                text=True
            )
            return True

        except subprocess.CalledProcessError:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_worktree_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_worktree_manager.py .claude/ultimate-team/git_integration/worktree_manager.py
git commit -m "feat: add worktree manager"
```

---

## Chunk 2: Hook 管理

### Task 2: 实现 Hook 管理器

**Files:**
- Create: `.claude/ultimate-team/git_integration/hook_manager.py`
- Create: `tests/test_hook_manager.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hook_manager.py -v`
Expected: FAIL with "HookManager not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/git_integration/hook_manager.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hook_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_hook_manager.py .claude/ultimate-team/git_integration/hook_manager.py
git commit -m "feat: add hook manager"
```

---

### Task 3: 创建自动化 Hooks

**Files:**
- Create: `.claude/ultimate-team/hooks/pre_task.py`
- Create: `.claude/ultimate-team/hooks/post_task.py`
- Create: `.claude/ultimate-team/hooks/pre_commit.py`

- [ ] **Step 1: Write pre_task hook**

```python
# .claude/ultimate-team/hooks/pre_task.py
#!/usr/bin/env python3
"""
任务前 Hook

在开始任务前执行：
1. 检查 Git 状态是否干净
2. 创建或切换到任务分支
3. 可选：创建 worktree
"""

import sys
import subprocess
from pathlib import Path

def main():
    task_id = sys.argv[1] if len(sys.argv) > 1 else None
    create_worktree = sys.argv[2] == "true" if len(sys.argv) > 2 else False

    # 检查 Git 状态
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        print("⚠️  工作区不干净，请先提交或暂存更改")
        return 1

    # 创建任务分支
    branch_name = f"task/{task_id}" if task_id else "task/new"

    if create_worktree:
        print(f"🔧 创建 worktree: {branch_name}")
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, f"../worktree-{branch_name}"],
            check=True
        )
    else:
        # 检查分支是否存在
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            capture_output=True
        )

        if result.returncode != 0:
            print(f"🔧 创建分支: {branch_name}")
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True
            )
        else:
            print(f"🔧 切换到分支: {branch_name}")
            subprocess.run(["git", "checkout", branch_name], check=True)

    print(f"✅ 任务环境准备完成: {branch_name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write post_task hook**

```python
# .claude/ultimate-team/hooks/post_task.py
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
```

- [ ] **Step 3: Write pre_commit hook**

```python
# .claude/ultimate-team/hooks/pre_commit.py
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
```

- [ ] **Step 4: Make hooks executable**

Run:
```bash
chmod +x .claude/ultimate-team/hooks/pre_task.py
chmod +x .claude/ultimate-team/hooks/post_task.py
chmod +x .claude/ultimate-team/hooks/pre_commit.py
```

- [ ] **Step 5: Create integration test**

```python
# tests/test_git_integration.py
import pytest
import subprocess
from pathlib import Path

def test_hook_execution():
    """测试 hook 执行"""
    # 测试 pre_task hook
    result = subprocess.run(
        ["python3", ".claude/ultimate-team/hooks/pre_task.py", "TASK-001", "false"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "任务环境准备完成" in result.stdout

def test_pre_commit_hook():
    """测试 pre-commit hook"""
    # 创建测试文件
    test_file = Path("test_temp.py")
    test_file.write_text("""
def hello():
    return "hello"
""")

    try:
        # 添加到 Git
        subprocess.run(["git", "add", "test_temp.py"])

        # 运行 pre-commit hook
        result = subprocess.run(
            ["python3", ".claude/ultimate-team/hooks/pre_commit.py"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "提交前检查通过" in result.stdout

    finally:
        # 清理
        test_file.unlink()
        subprocess.run(["git", "reset", "HEAD", "test_temp.py"])
```

- [ ] **Step 6: Commit**

```bash
git add .claude/ultimate-team/hooks/ tests/test_git_integration.py
git commit -m "feat: add automated hooks"
```

---

## Chunk 3: 分支策略和提交追踪

### Task 4: 实现分支策略

**Files:**
- Create: `.claude/ultimate-team/git_integration/branch_strategy.py`
- Create: `tests/test_branch_strategy.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_branch_strategy.py
import pytest
from ultimate_team.git_integration.branch_strategy import BranchStrategy, BranchType

def test_branch_naming():
    """测试分支命名"""
    strategy = BranchStrategy()

    # 功能分支
    feature_branch = strategy.create_branch_name(BranchType.FEATURE, "user-auth")
    assert feature_branch == "feature/user-auth"

    # 修复分支
    fix_branch = strategy.create_branch_name(BranchType.FIX, "login-bug")
    assert fix_branch == "fix/login-bug"

    # 任务分支
    task_branch = strategy.create_branch_name(BranchType.TASK, "TASK-001")
    assert task_branch == "task/TASK-001"

def test_validate_branch_name():
    """测试分支名验证"""
    strategy = BranchStrategy()

    # 有效分支名
    assert strategy.validate_branch_name("feature/user-auth") == True
    assert strategy.validate_branch_name("fix/bug-123") == True

    # 无效分支名
    assert strategy.validate_branch_name("invalid") == False
    assert strategy.validate_branch_name("") == False

def test_get_base_branch():
    """测试获取基础分支"""
    strategy = BranchStrategy()

    assert strategy.get_base_branch(BranchType.FEATURE) == "main"
    assert strategy.get_base_branch(BranchType.FIX) == "main"
    assert strategy.get_base_branch(BranchType.HOTFIX) == "production"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_branch_strategy.py -v`
Expected: FAIL with "BranchStrategy not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/git_integration/branch_strategy.py
from enum import Enum
from typing import Dict

class BranchType(Enum):
    """分支类型"""
    FEATURE = "feature"
    FIX = "fix"
    HOTFIX = "hotfix"
    TASK = "task"
    RELEASE = "release"
    EXPERIMENT = "experiment"

class BranchStrategy:
    """分支策略管理"""

    # 分支命名规则
    BRANCH_PATTERNS = {
        BranchType.FEATURE: "{type}/{feature}",
        BranchType.FIX: "{type}/{issue}",
        BranchType.HOTFIX: "{type}/{issue}",
        BranchType.TASK: "{type}/{task_id}",
        BranchType.RELEASE: "{type}/{version}",
        BranchType.EXPERIMENT: "experiment/{username}/{feature}"
    }

    # 基础分支映射
    BASE_BRANCHES = {
        BranchType.FEATURE: "main",
        BranchType.FIX: "main",
        BranchType.HOTFIX: "production",
        BranchType.TASK: "main",
        BranchType.RELEASE: "main",
        BranchType.EXPERIMENT: "main"
    }

    def create_branch_name(self, branch_type: BranchType, identifier: str) -> str:
        """创建分支名"""
        pattern = self.BRANCH_PATTERNS.get(branch_type, "{type}/{identifier}")

        return pattern.format(
            type=branch_type.value,
            feature=identifier,
            issue=identifier,
            task_id=identifier,
            version=identifier,
            username="user",  # TODO: 从配置获取
            identifier=identifier
        )

    def validate_branch_name(self, branch_name: str) -> bool:
        """验证分支名"""
        if not branch_name:
            return False

        # 检查是否符合类型/名称格式
        parts = branch_name.split("/", 1)

        if len(parts) != 2:
            return False

        branch_type = parts[0]

        # 检查是否是有效的分支类型
        try:
            BranchType(branch_type)
            return True
        except ValueError:
            return False

    def get_base_branch(self, branch_type: BranchType) -> str:
        """获取基础分支"""
        return self.BASE_BRANCHES.get(branch_type, "main")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_branch_strategy.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_branch_strategy.py .claude/ultimate-team/git_integration/branch_strategy.py
git commit -m "feat: add branch strategy"
```

---

### Task 5: 实现提交追踪

**Files:**
- Create: `.claude/ultimate-team/git_integration/commit_tracker.py`
- Create: `tests/test_commit_tracker.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_commit_tracker.py -v`
Expected: FAIL with "CommitTracker not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/git_integration/commit_tracker.py
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
```

- [ ] **Step 4: Create git_integration __init__.py**

```python
# .claude/ultimate-team/git_integration/__init__.py
from .worktree_manager import WorktreeManager, WorktreeInfo
from .hook_manager import HookManager
from .branch_strategy import BranchStrategy, BranchType
from .commit_tracker import CommitTracker, CommitInfo

__all__ = [
    'WorktreeManager',
    'WorktreeInfo',
    'HookManager',
    'BranchStrategy',
    'BranchType',
    'CommitTracker',
    'CommitInfo'
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_commit_tracker.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_commit_tracker.py .claude/ultimate-team/git_integration/commit_tracker.py .claude/ultimate-team/git_integration/__init__.py
git commit -m "feat: add commit tracker"
```

---

## Chunk 4: Git CLI 命令

### Task 6: 创建 Git CLI 命令

**Files:**
- Create: `.claude/ultimate-team/cli/git_commands.py`
- Create: `tests/test_git_commands.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_git_commands.py
import pytest
import subprocess
from ultimate_team.cli.git_commands import git_create_branch, git_status

def test_git_create_branch():
    """测试创建分支命令"""
    result = subprocess.run(
        ["python3", "-c", "from ultimate_team.cli.git_commands import git_create_branch; git_create_branch('test-branch')"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

def test_git_status():
    """测试状态命令"""
    result = subprocess.run(
        ["python3", "-c", "from ultimate_team.cli.git_commands import git_status; git_status()"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_git_commands.py -v`
Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
# .claude/ultimate-team/cli/git_commands.py
#!/usr/bin/env python3
"""
Git CLI 命令

提供便捷的 Git 操作命令
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ultimate_team.git_integration import (
    WorktreeManager,
    BranchStrategy,
    BranchType
)

def cmd_create_branch(args):
    """创建分支"""
    strategy = BranchStrategy()

    # 解析分支类型
    try:
        branch_type = BranchType(args.type)
    except ValueError:
        print(f"❌ 无效的分支类型: {args.type}")
        return 1

    # 生成分支名
    branch_name = strategy.create_branch_name(branch_type, args.identifier)

    print(f"🔧 创建分支: {branch_name}")

    # 获取基础分支
    base_branch = args.base or strategy.get_base_branch(branch_type)

    # 创建分支
    import subprocess
    try:
        subprocess.run(
            ["git", "checkout", "-b", branch_name, base_branch],
            check=True
        )
        print(f"✅ 分支创建成功: {branch_name}")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ 创建分支失败: {e}")
        return 1

def cmd_worktree(args):
    """Worktree 操作"""
    manager = WorktreeManager(".")

    if args.action == "create":
        worktree_path = manager.create(args.branch, args.base)

        if worktree_path:
            print(f"✅ Worktree 创建成功: {worktree_path}")
            return 0
        else:
            print("❌ Worktree 创建失败")
            return 1

    elif args.action == "list":
        worktrees = manager.list()

        print(f"📋 Worktree 列表 ({len(worktrees)} 个):")
        for wt in worktrees:
            print(f"  - {wt.branch} @ {wt.path}")

        return 0

    elif args.action == "remove":
        if manager.remove(args.branch):
            print(f"✅ Worktree 移除成功: {args.branch}")
            return 0
        else:
            print("❌ Worktree 移除失败")
            return 1

def main():
    parser = argparse.ArgumentParser(description="Git 工具命令")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # create-branch 命令
    branch_parser = subparsers.add_parser("create-branch", help="创建分支")
    branch_parser.add_argument("type", help="分支类型 (feature/fix/hotfix/task)")
    branch_parser.add_argument("identifier", help="标识符")
    branch_parser.add_argument("--base", help="基础分支")

    # worktree 命令
    worktree_parser = subparsers.add_parser("worktree", help="Worktree 操作")
    worktree_parser.add_argument("action", choices=["create", "list", "remove"], help="操作")
    worktree_parser.add_argument("--branch", help="分支名")
    worktree_parser.add_argument("--base", default="main", help="基础分支")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "create-branch":
        return cmd_create_branch(args)
    elif args.command == "worktree":
        return cmd_worktree(args)

    return 0

# 导出的便捷函数
def git_create_branch(branch_type: str, identifier: str, base: str = None):
    """创建分支（便捷函数）"""
    sys.argv = ["git", "create-branch", branch_type, identifier]
    if base:
        sys.argv.extend(["--base", base])

    return main()

def git_status():
    """显示 Git 状态（便捷函数）"""
    import subprocess
    subprocess.run(["git", "status"])

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Create cli __init__.py**

```python
# .claude/ultimate-team/cli/__init__.py
from .git_commands import git_create_branch, git_status

__all__ = ['git_create_branch', 'git_status']
```

- [ ] **Step 5: Make executable**

Run: `chmod +x .claude/ultimate-team/cli/git_commands.py`

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_git_commands.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/test_git_commands.py .claude/ultimate-team/cli/git_commands.py .claude/ultimate-team/cli/__init__.py
git commit -m "feat: add git CLI commands"
```

---

## 总结

**完成的组件**:
- ✅ Worktree 管理器（创建、列出、移除、清理）
- ✅ Hook 管理器（安装、移除、列出 hooks）
- ✅ 自动化 Hooks（pre_task、post_task、pre_commit）
- ✅ 分支策略（命名规则、验证、基础分支）
- ✅ 提交追踪（提交历史、统计信息）
- ✅ Git CLI 命令（分支创建、worktree 管理）

**完整系统总结**:

4 个独立实施计划已全部完成：

1. **Part 1: 核心路由系统** - 场景匹配、优先级排序、快速/智能路径决策
2. **Part 2: 任务管理系统** - 优先级队列、依赖解析、持久化、CLI 工具
3. **Part 3: 闭环执行器** - 开发 B、反馈 E、全流程 F 闭环、质量关卡
4. **Part 4: Git 集成** - Worktree、Hooks、分支策略、提交追踪

**系统已就绪，可以开始执行！**

使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 开始实施。
