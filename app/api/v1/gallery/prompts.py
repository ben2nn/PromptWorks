"""
画廊提示词API接口

基于现有的提示词API端点，为画廊展示优化
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.endpoints.prompts import list_prompts, get_prompt
from app.schemas.prompt import PromptRead
from app.models.prompt import MediaType

router = APIRouter()


@router.get("", response_model=List[PromptRead])
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
    try:
        # 直接调用现有的API端点
        return list_prompts(
            db=db, q=q, media_type=media_type, 
            limit=limit, offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取提示词列表失败")


@router.get("/{prompt_id}", response_model=PromptRead)
def get_gallery_prompt_detail(
    *,
    db: Session = Depends(get_db),
    prompt_id: int
):
    """
    获取画廊提示词详情
    
    基于现有的get_prompt接口，为画廊展示优化
    """
    try:
        # 直接调用现有的API端点
        return get_prompt(db=db, prompt_id=prompt_id)
    except HTTPException:
        # 重新抛出HTTP异常（如404）
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取提示词详情失败")