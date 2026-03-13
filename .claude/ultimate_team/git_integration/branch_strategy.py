# .claude/ultimate_team/git_integration/branch_strategy.py
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
