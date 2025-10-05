from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.task_queue import task_queue as _test_run_task_queue  # noqa: F401 - 确保队列初始化


def create_application() -> FastAPI:
    """Instantiate the FastAPI application."""

    # 初始化日志系统并输出应用启动信息
    configure_logging()
    app_logger = get_logger("promptworks.app")
    app_logger.info("FastAPI 应用初始化开始")

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # 注册自定义请求日志中间件，捕获每一次请求信息
    app.add_middleware(RequestLoggingMiddleware)
    allowed_origins = settings.BACKEND_CORS_ORIGINS or ["http://localhost:5173"]
    allow_credentials = settings.BACKEND_CORS_ALLOW_CREDENTIALS
    if "*" in allowed_origins:
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    app_logger.info("FastAPI 应用初始化完成")
    return app


app = create_application()
