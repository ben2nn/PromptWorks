"""
画廊API模块初始化

为画廊功能提供专门的API接口，基于现有FastAPI应用和数据模型
完全复用现有的API端点和服务层逻辑，不修改任何现有代码
"""
from fastapi import APIRouter

from .prompts import router as prompts_router
from .categories import router as categories_router
from .tags import router as tags_router
from .featured import router as featured_router
from .exceptions import GalleryResponse, gallery_exception_handler

# 创建画廊API主路由器
router = APIRouter(prefix="/gallery", tags=["gallery"])

# 注册各个子模块路由
router.include_router(prompts_router, prefix="/prompts", tags=["gallery-prompts"])
router.include_router(categories_router, prefix="/categories", tags=["gallery-categories"])
router.include_router(tags_router, prefix="/tags", tags=["gallery-tags"])
router.include_router(featured_router, prefix="/featured", tags=["gallery-featured"])

# 导出统一响应格式类供其他模块使用
__all__ = ["router", "GalleryResponse"]