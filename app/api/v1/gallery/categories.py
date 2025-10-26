"""
画廊分类API接口

基于现有的分类API端点，为画廊展示优化
"""

from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.api.v1.endpoints.prompt_classes import list_prompt_classes
from app.schemas import PromptClassStats
from .exceptions import (
    GalleryValidationError,
    GalleryDatabaseError,
    safe_execute
)

router = APIRouter()


@router.get("")
def get_gallery_categories(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """
    获取画廊分类列表
    
    基于现有的list_prompt_classes接口，为画廊展示优化
    """
    # 参数验证
    if limit <= 0 or limit > 200:
        raise GalleryValidationError("返回数量限制必须在1-200之间")
    
    try:
        # 直接调用现有的API端点
        result = safe_execute(
            list_prompt_classes,
            db=db, q=None, limit=limit, offset=0
        )
        
        # 转换为标准画廊响应格式
        from .exceptions import GalleryResponse
        return GalleryResponse.success(
            data=[PromptClassStats.model_validate(category) for category in result]
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except SQLAlchemyError:
        raise GalleryDatabaseError("查询分类列表时数据库错误")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="获取分类列表失败"
        )