# .claude/ultimate-team/core/scenario_matcher.py
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import os

@dataclass
class MatchResult:
    """匹配结果"""
    scenario_id: str
    confidence: float
    matched_keywords: List[str] = field(default_factory=list)

    def __getitem__(self, key):
        """支持字典式访问"""
        return getattr(self, key)

class ScenarioMatcher:
    """场景匹配器 - 匹配用户输入到预设场景"""

    def __init__(self):
        # 从配置文件加载场景定义
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> Dict:
        """加载场景配置"""
        try:
            import yaml
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 从 .claude/ultimate_team/core/ 向上两级到 .claude，然后到 ultimate_team/scenarios/
            claude_dir = os.path.dirname(os.path.dirname(current_dir))
            config_path = os.path.join(claude_dir, "ultimate_team", "scenarios", "scenarios.yaml")

            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，返回默认场景
            return {
                "maintenance": {
                    "triggers": ["查看", "检查", "状态"],
                    "priority": 7,
                    "strong_match": False,
                    "default": True
                }
            }
        except Exception as e:
            # 其他错误也返回默认场景
            return {
                "maintenance": {
                    "triggers": ["查看", "检查", "状态"],
                    "priority": 7,
                    "strong_match": False,
                    "default": True
                }
            }

    def match(self, user_input: str) -> MatchResult:
        """匹配用户输入到场景"""
        # 收集所有匹配的场景
        all_matches = []

        for scenario_id, config in self.scenarios.items():
            # 检查触发词 - 按在输入字符串中出现的顺序排序
            matches = []
            for trigger in config["triggers"]:
                if trigger in user_input:
                    matches.append(trigger)

            if not matches:
                continue

            # 按在输入字符串中的位置排序
            matches.sort(key=lambda x: user_input.index(x))

            # 计算匹配置信度
            confidence = len(matches) / len(config["triggers"])

            # 强匹配加分
            if config.get("strong_match"):
                for trigger in matches:
                    if user_input.startswith(trigger):
                        confidence += 0.5
                        break

            all_matches.append({
                "scenario_id": scenario_id,
                "confidence": confidence,
                "matched_keywords": matches,
                "priority": config.get("priority", 999)
            })

        # 如果没有匹配，返回默认场景
        if not all_matches:
            return MatchResult(
                scenario_id="maintenance",
                confidence=1.0,
                matched_keywords=[]
            )

        # 按置信度排序（降序），然后按优先级排序（优先级数字越小越高）
        all_matches.sort(key=lambda x: (-x["confidence"], x["priority"]))

        # 返回最高优先级的匹配
        best = all_matches[0]
        return MatchResult(
            scenario_id=best["scenario_id"],
            confidence=best["confidence"],
            matched_keywords=best["matched_keywords"]
        )
