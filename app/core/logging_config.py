from __future__ import annotations

import logging
from zoneinfo import ZoneInfo
from datetime import datetime

from app.core.config import settings

# 定义北京时间时区对象，确保所有日志时间统一为北京时区
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
# 定义公共日志格式，包含日志级别、时间、模块名称与具体消息内容
LOG_FORMAT = "[%(levelname)s] %(asctime)s %(name)s - %(message)s"
# 默认时间格式，便于读取
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class BeijingTimeFormatter(logging.Formatter):
    """自定义日志格式化器，用于强制日志时间显示为北京时间。"""

    def __init__(
        self, fmt: str, datefmt: str | None = None, timezone: ZoneInfo | None = None
    ) -> None:
        # 记录目标时区，默认使用北京时区
        super().__init__(fmt=fmt, datefmt=datefmt)
        self._timezone = timezone or BEIJING_TZ

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        # 使用记录生成时间与指定时区构造 datetime，以便格式化输出
        current_time = datetime.fromtimestamp(record.created, tz=self._timezone)
        return current_time.strftime(datefmt or DEFAULT_DATE_FORMAT)


def _build_console_handler() -> logging.Handler:
    """构建标准输出日志处理器，负责控制日志级别与格式。"""

    console_handler = logging.StreamHandler()
    # 测试模式下允许打印 DEBUG 日志，其他模式仅打印 INFO 及以上日志
    handler_level = logging.DEBUG if settings.APP_TEST_MODE else logging.INFO
    console_handler.setLevel(handler_level)
    console_handler.setFormatter(BeijingTimeFormatter(LOG_FORMAT, DEFAULT_DATE_FORMAT))
    # 标记该处理器，避免重复添加
    setattr(console_handler, "_is_promptworks_handler", True)
    return console_handler


def configure_logging() -> None:
    """初始化全局日志配置，仅在首次调用时生效。"""

    root_logger = logging.getLogger()
    # 如果已经存在我们自定义的处理器，则无需重复配置
    for handler in root_logger.handlers:
        if getattr(handler, "_is_promptworks_handler", False):
            return

    # 统一提升根日志器的级别为 DEBUG，交由处理器判断是否真正输出
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(_build_console_handler())

    _disable_uvicorn_logs()


def _disable_uvicorn_logs() -> None:
    """关闭 FastAPI/Uvicorn 默认日志，避免重复输出。"""

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = False
        logger.disabled = True


def get_logger(name: str) -> logging.Logger:
    """提供模块级日志记录器，确保使用统一配置。"""

    configure_logging()
    return logging.getLogger(name)
