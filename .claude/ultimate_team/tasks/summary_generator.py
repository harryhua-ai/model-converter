# .claude/ultimate_team/tasks/summary_generator.py
from typing import List, Dict
from datetime import datetime
from ..task_manager.task import Task, TaskStatus

class SummaryGenerator:
    """Markdown 摘要生成器"""

    def generate(self, tasks: List[Task]) -> str:
        """生成任务摘要"""
        stats = self.generate_statistics(tasks)

        lines = [
            "# 任务摘要",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 统计概览",
            "",
            f"- **总任务数**: {stats['total']}",
            f"- **已完成**: {stats['completed']}",
            f"- **进行中**: {stats['in_progress']}",
            f"- **待处理**: {stats['pending']}",
            f"- **已失败**: {stats['failed']}",
            "",
            "## 任务列表",
            ""
        ]

        # 按状态分组
        grouped = self._group_by_status(tasks)

        for status, status_tasks in grouped.items():
            lines.append(f"### {self._status_name(status)}")
            lines.append("")

            if not status_tasks:
                lines.append("*无任务*")
                lines.append("")
                continue

            for task in status_tasks:
                lines.append(f"#### {task.task_id}: {task.subject}")
                lines.append("")
                if task.description:
                    lines.append(f"- **描述**: {task.description}")
                if task.owner:
                    lines.append(f"- **负责人**: {task.owner}")
                if task.dependencies:
                    lines.append(f"- **依赖**: {', '.join(task.dependencies)}")
                if task.error:
                    lines.append(f"- **错误**: {task.error}")
                lines.append("")

        return "\n".join(lines)

    def generate_statistics(self, tasks: List[Task]) -> Dict[str, int]:
        """生成统计信息"""
        return {
            "total": len(tasks),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "blocked": len([t for t in tasks if t.status == TaskStatus.BLOCKED])
        }

    def save(self, tasks: List[Task], file_path: str) -> None:
        """保存摘要到文件"""
        summary = self.generate(tasks)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary)

    def _group_by_status(self, tasks: List[Task]) -> Dict[TaskStatus, List[Task]]:
        """按状态分组"""
        grouped = {}
        for task in tasks:
            if task.status not in grouped:
                grouped[task.status] = []
            grouped[task.status].append(task)
        return grouped

    def _status_name(self, status: TaskStatus) -> str:
        """状态名称"""
        names = {
            TaskStatus.PENDING: "待处理",
            TaskStatus.IN_PROGRESS: "进行中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "已失败",
            TaskStatus.BLOCKED: "已阻塞"
        }
        return names.get(status, str(status))
