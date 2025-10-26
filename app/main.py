from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.__version__ import get_version
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.task_queue import task_queue as _test_run_task_queue  # noqa: F401 - 确保队列初始化
from app.api.v1.gallery.exceptions import GalleryException, gallery_exception_handler, GalleryResponse


class StaticFilesCORSMiddleware(BaseHTTPMiddleware):
    """为静态文件路径添加 CORS 响应头的中间件"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 如果是静态文件路径，添加 CORS 响应头
        if request.url.path.startswith("/api/v1/files/"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response


def create_application() -> FastAPI:
    """Instantiate the FastAPI application."""

    # 初始化日志系统并输出应用启动信息
    configure_logging()
    app_logger = get_logger("promptworks.app")
    app_logger.info("FastAPI 应用初始化开始")

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=get_version(),
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        redirect_slashes=False,  # 禁用自动重定向，避免 CORS 问题
    )

    # 注册自定义请求日志中间件，捕获每一次请求信息
    app.add_middleware(RequestLoggingMiddleware)
    
    # 添加静态文件 CORS 中间件（必须在 CORSMiddleware 之前）
    app.add_middleware(StaticFilesCORSMiddleware)
    
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
    
    # 挂载静态文件目录（用于访问上传的附件）
    uploads_path = Path(settings.FILE_STORAGE_PATH)
    if uploads_path.exists():
        app.mount(
            f"{settings.API_V1_STR}/files",
            StaticFiles(directory=str(uploads_path)),
            name="uploads"
        )
        app_logger.info(f"静态文件目录已挂载: {uploads_path}")
    else:
        app_logger.warning(f"上传目录不存在: {uploads_path}")
    
    # 添加画廊API异常处理器
    app.add_exception_handler(GalleryException, gallery_exception_handler)
    
    # 添加FastAPI参数验证错误处理器（仅对画廊API路径）
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # 只对画廊API路径应用标准化错误格式
        if request.url.path.startswith("/api/v1/gallery/"):
            return JSONResponse(
                status_code=422,
                content=GalleryResponse.error(
                    "VALIDATION_ERROR",
                    "请求参数验证失败",
                    details=[{"field": err["loc"][-1], "message": err["msg"]} for err in exc.errors()]
                )
            )
        # 对其他路径保持原有的错误格式
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )
    
    app_logger.info("FastAPI 应用初始化完成")
    return app


app = create_application()
