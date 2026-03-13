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
