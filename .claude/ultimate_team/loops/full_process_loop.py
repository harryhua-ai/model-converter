# .claude/ultimate_team/loops/full_process_loop.py
from .base_loop import BaseLoop, LoopStage
from typing import Dict, Any, List

class FullProcessLoop(BaseLoop):
    """
    全流程闭环（F 闭环）

    9 个阶段：需求 → 设计 → 实现 → 测试 → 审查 → 文档 → 部署 → 监控 → 维护
    """

    def _define_stages(self) -> List[LoopStage]:
        return [
            LoopStage("requirements", "需求分析", entry_conditions=["项目启动"]),
            LoopStage("design", "系统设计", entry_conditions=["需求明确"]),
            LoopStage("implementation", "功能实现", entry_conditions=["设计完成"]),
            LoopStage("testing", "测试验证", entry_conditions=["实现完成"]),
            LoopStage("review", "代码审查", entry_conditions=["测试通过"]),
            LoopStage("documentation", "文档编写", entry_conditions=["审查通过"]),
            LoopStage("deployment", "部署上线", entry_conditions=["文档完成"]),
            LoopStage("monitoring", "运行监控", entry_conditions=["已部署"]),
            LoopStage("maintenance", "运维维护", entry_conditions=["运行稳定"])
        ]

    async def _execute_stage(self, stage: LoopStage, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段"""
        stage_id = stage.stage_id
        completed_stages = self._get_completed_stages(context)

        stage_result = await self._execute_stage_impl(stage_id, context)
        stage_result["completed_before"] = completed_stages

        context[stage_id + "_stage"] = stage_result
        return context

    async def _execute_stage_impl(self, stage_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """阶段实现"""
        # TODO: 每个阶段的实际实现
        return {
            "status": "completed",
            "message": f"{stage_id} 阶段已完成",
            "artifacts": []
        }

    def _get_completed_stages(self, context: Dict[str, Any]) -> List[str]:
        """获取已完成的阶段列表"""
        completed = []
        for key in context.keys():
            if key.endswith("_stage"):
                stage_name = key.replace("_stage", "")
                completed.append(stage_name)
        return completed
