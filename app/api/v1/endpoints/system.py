"""
系统信息相关 API 端点
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.__version__ import get_version, get_version_info, VERSION_HISTORY


router = APIRouter()


class VersionResponse(BaseModel):
    """版本信息响应模型"""
    version: str
    version_info: tuple
    history: dict


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
    message: str


@router.get("/version", response_model=VersionResponse, summary="获取版本信息")
async def get_system_version():
    """
    获取系统版本信息
    
    返回当前系统的版本号、版本信息元组和版本历史记录
    """
    return VersionResponse(
        version=get_version(),
        version_info=get_version_info(),
        history=VERSION_HISTORY
    )


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """
    系统健康检查
    
    返回系统运行状态和版本信息
    """
    return HealthResponse(
        status="healthy",
        version=get_version(),
        message="PromptWorks 系统运行正常"
    )