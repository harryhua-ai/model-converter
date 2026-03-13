"""
日志配置模块
使用 structlog 进行结构化日志记录
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import settings


def add_log_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加日志级别"""
    if "level" not in event_dict:
        event_dict["level"] = method_name.upper()
    else:
        event_dict["level"] = str(event_dict["level"]).upper()
    return event_dict


def setup_logging() -> None:
    """配置结构化日志"""

    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # 配置 structlog（简化版本，避免 PrintLogger 兼容性问题）
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_log_level,
    ]

    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
