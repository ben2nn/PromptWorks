"""
画廊API异常处理模块

提供统一的异常处理和响应格式化功能
"""

from typing import Any, Dict
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class GalleryException(Exception):
    """画廊API基础异常类"""
    
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class GalleryNotFoundError(GalleryException):
    """资源不存在异常"""
    
    def __init__(self, resource: str = "资源"):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource}不存在",
            status_code=404
        )


class GalleryValidationError(GalleryException):
    """参数验证异常"""
    
    def __init__(self, message: str = "请求参数验证失败"):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400
        )


class GalleryDatabaseError(GalleryException):
    """数据库操作异常"""
    
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(
            code="DATABASE_ERROR",
            message=message,
            status_code=500
        )


class GalleryResponse:
    """画廊API统一响应格式"""
    
    @staticmethod
    def success(data: Any = None, pagination: Dict[str, Any] = None) -> Dict[str, Any]:
        """成功响应格式"""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if pagination:
            response["pagination"] = pagination
        return response
    
    @staticmethod
    def error(code: str, message: str, details: Any = None) -> Dict[str, Any]:
        """错误响应格式"""
        error_response = {
            "success": False,
            "error": {
                "code": code,
                "message": message
            }
        }
        if details:
            error_response["error"]["details"] = details
        return error_response


def handle_gallery_exception(exc: Exception) -> JSONResponse:
    """
    处理画廊API异常，返回标准化的错误响应
    
    Args:
        exc: 异常对象
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    
    # 处理自定义画廊异常
    if isinstance(exc, GalleryException):
        logger.warning(f"画廊API异常: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content=GalleryResponse.error(exc.code, exc.message)
        )
    
    # 处理FastAPI HTTP异常
    if isinstance(exc, HTTPException):
        # 根据状态码确定错误类型
        if exc.status_code == 404:
            code = "RESOURCE_NOT_FOUND"
        elif exc.status_code == 400:
            code = "VALIDATION_ERROR"
        elif exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 429:
            code = "RATE_LIMIT_EXCEEDED"
        else:
            code = "HTTP_ERROR"
            
        logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=GalleryResponse.error(code, str(exc.detail))
        )
    
    # 处理数据库异常
    if isinstance(exc, IntegrityError):
        logger.error(f"数据库完整性异常: {str(exc)}")
        return JSONResponse(
            status_code=400,
            content=GalleryResponse.error("DATABASE_INTEGRITY_ERROR", "数据完整性约束违反")
        )
    
    if isinstance(exc, SQLAlchemyError):
        logger.error(f"数据库异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=GalleryResponse.error("DATABASE_ERROR", "数据库操作失败")
        )
    
    # 处理其他未知异常
    logger.error(f"未知异常: {type(exc).__name__} - {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=GalleryResponse.error("INTERNAL_SERVER_ERROR", "服务器内部错误")
    )


def gallery_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    画廊API全局异常处理器
    
    Args:
        request: FastAPI请求对象
        exc: 异常对象
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    return handle_gallery_exception(exc)


def safe_execute(func, *args, **kwargs):
    """
    安全执行函数，自动处理异常
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果
        
    Raises:
        GalleryException: 转换后的画廊异常
    """
    try:
        return func(*args, **kwargs)
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except IntegrityError as e:
        logger.error(f"数据库完整性异常: {str(e)}")
        raise GalleryDatabaseError("数据完整性约束违反")
    except SQLAlchemyError as e:
        logger.error(f"数据库异常: {str(e)}")
        raise GalleryDatabaseError("数据库操作失败")
    except Exception as e:
        logger.error(f"未知异常: {type(e).__name__} - {str(e)}")
        raise GalleryException("INTERNAL_ERROR", "服务器内部错误", 500)