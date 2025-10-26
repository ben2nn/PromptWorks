"""
画廊提示词API接口

基于现有的提示词API端点，为画廊展示优化
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.api.v1.endpoints.prompts import list_prompts, get_prompt
from app.schemas.prompt import PromptRead
from app.models.prompt import MediaType
from .exceptions import (
    GalleryResponse, 
    GalleryNotFoundError, 
    GalleryValidationError,
    GalleryDatabaseError,
    safe_execute
)

router = APIRouter()


@router.get("")
def get_gallery_prompts(
    *,
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="搜索关键词"),
    media_type: Optional[MediaType] = Query(None, description="媒体类型筛选"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取画廊提示词列表
    
    基于现有的list_prompts接口，为画廊展示优化
    """
    # 参数验证
    if limit <= 0 or limit > 100:
        raise GalleryValidationError("每页数量必须在1-100之间")
    
    if offset < 0:
        raise GalleryValidationError("偏移量不能为负数")
    
    if q is not None and len(q.strip()) == 0:
        raise GalleryValidationError("搜索关键词不能为空")
    
    try:
        # 直接调用现有的API端点
        result = safe_execute(
            list_prompts,
            db=db, q=q, media_type=media_type, 
            limit=limit, offset=offset
        )
        
        # 转换为标准画廊响应格式
        return GalleryResponse.success(
            data=[PromptRead.model_validate(prompt) for prompt in result],
            pagination={
                "page": (offset // limit) + 1,
                "pageSize": limit,
                "total": len(result),  # 这里简化处理，实际应该查询总数
                "totalPages": 1  # 简化处理
            }
        )
    except HTTPException:
        # 重新抛出HTTP异常（保持原有错误处理）
        raise
    except SQLAlchemyError:
        raise GalleryDatabaseError("查询提示词列表时数据库错误")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="获取提示词列表失败"
        )


@router.get("/{prompt_id}")
def get_gallery_prompt_detail(
    *,
    db: Session = Depends(get_db),
    prompt_id: int
):
    """
    获取画廊提示词详情
    
    基于现有的get_prompt接口，为画廊展示优化
    """
    # 参数验证
    if prompt_id <= 0:
        raise GalleryValidationError("提示词ID必须为正整数")
    
    try:
        # 直接调用现有的API端点
        result = safe_execute(get_prompt, db=db, prompt_id=prompt_id)
        
        # 转换为标准画廊响应格式
        return GalleryResponse.success(
            data=PromptRead.model_validate(result)
        )
    except HTTPException as e:
        # 转换404错误为画廊标准格式
        if e.status_code == 404:
            raise GalleryNotFoundError("提示词")
        # 重新抛出其他HTTP异常
        raise
    except SQLAlchemyError:
        raise GalleryDatabaseError("查询提示词详情时数据库错误")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="获取提示词详情失败"
        )