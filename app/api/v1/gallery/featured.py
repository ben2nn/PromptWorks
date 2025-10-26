"""
画廊精选API接口

基于现有接口，提供精选提示词功能
"""

from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.api.v1.endpoints.prompts import list_prompts
from app.schemas.prompt import PromptRead
from .exceptions import (
    GalleryValidationError,
    GalleryDatabaseError,
    safe_execute
)

router = APIRouter()


@router.get("")
def get_featured_prompts(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="精选数量")
):
    """
    获取精选提示词
    
    基于现有接口，返回最新更新的提示词作为精选内容
    """
    # 参数验证
    if limit <= 0 or limit > 50:
        raise GalleryValidationError("精选数量必须在1-50之间")
    
    try:
        # 调用现有接口获取最新提示词作为精选
        result = safe_execute(
            list_prompts,
            db=db, q=None, media_type=None,
            limit=limit, offset=0
        )
        
        # 转换为标准画廊响应格式
        from .exceptions import GalleryResponse
        return GalleryResponse.success(
            data=[PromptRead.model_validate(prompt) for prompt in result]
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except SQLAlchemyError:
        raise GalleryDatabaseError("查询精选提示词时数据库错误")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="获取精选提示词失败"
        )