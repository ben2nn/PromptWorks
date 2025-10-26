"""
画廊标签API接口

基于现有的标签API端点，为画廊展示优化
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.api.v1.endpoints.prompt_tags import list_prompt_tags
from app.schemas import PromptTagListResponse
from .exceptions import (
    GalleryDatabaseError,
    safe_execute
)

router = APIRouter()


@router.get("")
def get_gallery_tags(*, db: Session = Depends(get_db)):
    """
    获取画廊标签列表
    
    基于现有的list_prompt_tags接口，为画廊展示优化
    """
    try:
        # 直接调用现有的API端点
        result = safe_execute(list_prompt_tags, db=db)
        
        # 转换为标准画廊响应格式
        from .exceptions import GalleryResponse
        return GalleryResponse.success(
            data=PromptTagListResponse.model_validate(result)
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except SQLAlchemyError:
        raise GalleryDatabaseError("查询标签列表时数据库错误")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="获取标签列表失败"
        )