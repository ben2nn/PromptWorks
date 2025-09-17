from __future__ import annotations

import logging
import time
from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.logging_config import get_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """负责在每次 HTTP 请求完成后记录关键访问信息的中间件。"""

    def __init__(self, app: ASGIApp) -> None:
        # 初始化父类并准备日志记录器
        super().__init__(app)
        self._logger = get_logger("promptworks.middleware.request")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 记录请求开始时间，方便统计耗时
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
        except Exception:
            # 出现异常时记录完整堆栈，协助定位问题
            elapsed = (time.perf_counter() - start_time) * 1000
            self._logger.exception(
                "请求处理异常: %s %s 来自 %s 耗时 %.2fms",
                method,
                path,
                client_host,
                elapsed,
            )
            raise

        elapsed = (time.perf_counter() - start_time) * 1000
        # 标准请求日志，包含方法、路径、客户端、状态码与耗时
        self._logger.info(
            "请求完成: %s %s 来自 %s 状态码 %s 耗时 %.2fms",
            method,
            path,
            client_host,
            response.status_code,
            elapsed,
        )

        # DEBUG 模式下附加更多请求上下文，便于调试
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("请求查询参数: %s", dict(request.query_params))

        return response
