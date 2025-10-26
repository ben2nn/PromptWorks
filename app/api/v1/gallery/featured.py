"""
画廊精选API接口

基于现有接口，提供精选提示词功能
"""

from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.endpoints.prompts import list_prompts
from app.schemas.prompt import PromptRead

router = APIRouter()


@router.get("", response_model=List[PromptRead])
def get_featured_prompts(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="精选数量")
):
    """
    获取精选提示词
    
    基于现有接口，返回最新更新的提示词作为精选内容
    """
    try:
        # 调用现有接口获取最新提示词作为精选
        return list_prompts(
            db=db, q=None, media_type=None,
            limit=limit, offset=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取精选提示词失败")