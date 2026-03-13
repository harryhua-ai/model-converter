# .claude/ultimate_team/execution/loop_executor.py
from typing import Dict, Any, List, Tuple
from ..loops.base_loop import BaseLoop
from ..quality.gates import QualityGate, GateResult, GateStatus
from ..quality.verifiers import BaseVerifier

class LoopExecutor:
    """闭环执行器"""

    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []

    async def execute(
        self,
        loop: BaseLoop,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行闭环"""
        execution_record = {
            "loop_type": loop.__class__.__name__,
            "start_context": context.copy(),
            "timestamp": self._get_timestamp()
        }

        try:
            result_context = await loop.start(context)

            execution_record.update({
                "success": True,
                "context": result_context,
                "state": loop.state.name
            })

        except Exception as e:
            execution_record.update({
                "success": False,
                "error": str(e),
                "state": loop.state.name
            })

        self.execution_history.append(execution_record)
        return execution_record

    async def execute_with_gates(
        self,
        loop: BaseLoop,
        context: Dict[str, Any],
        quality_gates: List[Tuple[QualityGate, BaseVerifier, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """执行闭环并验证质量关卡"""
        execution_record = {
            "loop_type": loop.__class__.__name__,
            "start_context": context.copy(),
            "quality_gate_count": len(quality_gates),
            "timestamp": self._get_timestamp()
        }

        try:
            # 执行闭环
            result_context = await loop.start(context)

            # 验证质量关卡
            gate_results = []
            all_passed = True

            for gate, verifier, verifier_kwargs in quality_gates:
                result = await verifier.verify(gate, **verifier_kwargs)
                gate_results.append({
                    "gate_id": gate.gate_id,
                    "status": result.status.name,
                    "message": result.message
                })

                if result.should_block():
                    all_passed = False

            execution_record.update({
                "success": all_passed,
                "context": result_context,
                "quality_gate_results": gate_results,
                "state": loop.state.name
            })

        except Exception as e:
            execution_record.update({
                "success": False,
                "error": str(e),
                "state": loop.state.name
            })

        self.execution_history.append(execution_record)
        return execution_record

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """获取执行历史"""
        return self.execution_history.copy()

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
