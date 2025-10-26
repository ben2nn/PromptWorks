"""
画廊标签API接口

基于现有的标签API端点，为画廊展示优化
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.endpoints.prompt_tags import list_prompt_tags
from app.schemas import PromptTagListResponse

router = APIRouter()


@router.get("", response_model=PromptTagListResponse)
def get_gallery_tags(*, db: Session = Depends(get_db)):
    """
    获取画廊标签列表
    
    基于现有的list_prompt_tags接口，为画廊展示优化
    """
    try:
        # 直接调用现有的API端点
        return list_prompt_tags(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取标签列表失败")