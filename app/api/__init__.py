"""
API接口模块初始化

为画廊功能提供专门的API接口
"""
from fastapi import APIRouter

# 创建画廊API路由器
gallery_router = APIRouter(prefix="/gallery", tags=["gallery"])

def init_gallery_api():
    """初始化画廊API模块"""
    # 导入画廊路由
    from . import gallery
    
    # 注册画廊路由
    gallery_router.include_router(gallery.router)
    
    return gallery_router