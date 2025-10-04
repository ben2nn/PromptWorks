from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import RequestLoggingMiddleware


def _create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ok")
    async def ok_endpoint():  # pragma: no cover - FastAPI 生成代码路径
        return {"status": "ok"}

    @app.get("/error")
    async def error_endpoint():
        raise RuntimeError("middleware error path")

    return app


def test_request_logging_middleware_logs_debug(caplog: pytest.LogCaptureFixture):
    app = _create_app()
    client = TestClient(app)

    logger_name = "promptworks.middleware.request"
    with caplog.at_level(logging.DEBUG, logger=logger_name):
        response = client.get("/ok", params={"q": "test"})

    assert response.status_code == 200
    info_messages = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.INFO
    ]
    assert any("请求完成" in message for message in info_messages)
    debug_messages = [
        record.getMessage()
        for record in caplog.records
        if record.levelno == logging.DEBUG
    ]
    assert any("请求查询参数" in message for message in debug_messages)


def test_request_logging_middleware_logs_exception(caplog: pytest.LogCaptureFixture):
    app = _create_app()
    client = TestClient(app, raise_server_exceptions=False)

    logger_name = "promptworks.middleware.request"
    with caplog.at_level(logging.ERROR, logger=logger_name):
        response = client.get("/error")

    assert response.status_code == 500
    error_messages = [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.ERROR
    ]
    assert any("请求处理异常" in message for message in error_messages)
