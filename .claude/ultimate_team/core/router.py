# .claude/ultimate_team/core/router.py
from typing import Dict, Tuple, Optional
from .scenario_matcher import ScenarioMatcher


class ScenarioRouter:
    """场景路由器

    负责分析用户输入并决定使用快速路径还是智能路径：
    - 快速路径（FAST_PATH）：常见场景，直接使用预设配置
    - 智能路径（SMART_PATH）：复杂或罕见场景，需要动态规划
    """

    def __init__(self):
        self.matcher = ScenarioMatcher()

    def analyze(self, user_input: str) -> Dict:
        """分析用户需求

        Args:
            user_input: 用户输入的自然语言描述

        Returns:
            包含以下字段的字典：
            - intent: 原始用户输入
            - scenario_id: 匹配的场景ID
            - confidence: 匹配置信度 (0-1)
            - is_common_scenario: 是否为常见场景（置信度>0.7且非复杂）
            - complexity: 复杂度评估（simple/medium/complex）
        """
        # 使用场景匹配器
        match_result = self.matcher.match(user_input)

        # 分析复杂度
        complexity = self._assess_complexity(user_input)

        # 判断是否为常见场景：需要足够的置信度且不是复杂场景
        is_common = match_result.confidence > 0.7 and complexity != "complex"

        return {
            "intent": user_input,
            "scenario_id": match_result.scenario_id,
            "confidence": match_result.confidence,
            "is_common_scenario": is_common,
            "complexity": complexity
        }

    def _assess_complexity(self, user_input: str) -> str:
        """评估输入复杂度

        评估规则：
        - simple: 单词数<10 且无多任务标志
        - medium: 单词数10-20 且无多任务标志
        - complex: 单词数>20 或包含多任务标志

        Args:
            user_input: 用户输入

        Returns:
            复杂度级别（simple/medium/complex）
        """
        # 包含"同时"、"并且"、"加上"等多任务标志
        multi_task_indicators = ["同时", "并且", "加上"]
        has_multi_task = any(word in user_input for word in multi_task_indicators)

        # 按空格分词计算单词数
        word_count = len(user_input.split())

        if word_count < 10 and not has_multi_task:
            return "simple"
        elif word_count > 20 or has_multi_task:
            return "complex"
        else:
            return "medium"

    def route(self, analysis: Dict) -> Tuple[str, Optional[Dict]]:
        """路由决策

        根据分析结果决定使用快速路径还是智能路径。

        Args:
            analysis: analyze() 方法返回的分析结果

        Returns:
            元组 (路径类型, 场景配置)：
            - 路径类型: "FAST_PATH" 或 "SMART_PATH"
            - 场景配置: 快速路径返回场景配置字典，智能路径返回 None
        """
        if analysis["is_common_scenario"]:
            # 快速路径：使用预设场景配置
            scenario = self._get_scenario_config(analysis["scenario_id"])
            return "FAST_PATH", scenario
        else:
            # 智能路径：需要动态规划和推理
            return "SMART_PATH", None

    def _get_scenario_config(self, scenario_id: str) -> Optional[Dict]:
        """获取场景配置

        Args:
            scenario_id: 场景ID

        Returns:
            场景配置字典，如果场景不存在则返回 None
        """
        try:
            from ultimate_team.scenarios import load_scenarios
            scenarios = load_scenarios()

            if scenario_id in scenarios:
                config = scenarios[scenario_id].copy()
                # 添加 scenario_id 字段便于后续使用
                config["scenario_id"] = scenario_id
                return config
            else:
                return None
        except Exception:
            # 如果加载失败，返回 None
            return None
