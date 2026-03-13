# .claude/ultimate_team/scenarios/__init__.py
"""场景配置模块

提供场景配置加载功能，支持8种预设场景：
1. new_feature - 新功能开发
2. bugfix - Bug修复
3. refactor - 代码重构
4. performance - 性能优化
5. testing - 测试开发
6. security_review - 安全审查
7. documentation - 文档更新
8. maintenance - 常规维护
"""

import os
import yaml
from typing import Dict, Any


def load_scenarios() -> Dict[str, Dict[str, Any]]:
    """加载场景配置文件

    Returns:
        场景配置字典，键为场景ID，值为场景配置

    Raises:
        FileNotFoundError: 当配置文件不存在时
        yaml.YAMLError: 当YAML解析失败时
    """
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "scenarios.yaml")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            scenarios = yaml.safe_load(f)

        # 验证必需字段
        for scenario_id, config in scenarios.items():
            required_fields = ['name', 'triggers', 'priority', 'agents', 'skills', 'closed_loops', 'estimated_time']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"场景 {scenario_id} 缺少必需字段: {field}")

        return scenarios

    except FileNotFoundError:
        raise FileNotFoundError(
            f"场景配置文件不存在: {config_path}\n"
            "请确保 scenarios.yaml 文件位于 .claude/ultimate_team/scenarios/ 目录下"
        )
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"YAML 解析失败: {e}")


__all__ = ['load_scenarios']
