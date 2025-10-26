"""
画廊分类API接口

基于现有的分类API端点，为画廊展示优化
"""

from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.endpoints.prompt_classes import list_prompt_classes
from app.schemas import PromptClassStats

router = APIRouter()


@router.get("", response_model=List[PromptClassStats])
def get_gallery_categories(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """
    获取画廊分类列表
    
    基于现有的list_prompt_classes接口，为画廊展示优化
    """
    try:
        # 直接调用现有的API端点
        return list_prompt_classes(
            db=db, q=None, limit=limit, offset=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取分类列表失败")