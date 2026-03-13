# .claude/ultimate_team/git_integration/__init__.py
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
