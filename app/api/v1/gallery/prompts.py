"""
画廊提示词API接口

基于现有的提示词API端点，为画廊展示优化
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.api.v1.endpoints.prompts import get_prompt
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
    tags: Optional[str] = Query(None, description="标签ID列表，逗号分隔"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取画廊提示词列表
    
    基于现有的list_prompts接口，为画廊展示优化
    支持标签筛选和总数统计
    """
    # 参数验证
    if limit <= 0 or limit > 100:
        raise GalleryValidationError("每页数量必须在1-100之间")
    
    if offset < 0:
        raise GalleryValidationError("偏移量不能为负数")
    
    if q is not None and len(q.strip()) == 0:
        raise GalleryValidationError("搜索关键词不能为空")
    
    try:
        from sqlalchemy import select, func
        from app.models.prompt import Prompt, PromptClass
        
        # 构建基础查询
        stmt = select(Prompt).options(
            joinedload(Prompt.prompt_class),
            joinedload(Prompt.current_version),
            selectinload(Prompt.versions),
            selectinload(Prompt.tags),
            selectinload(Prompt.attachments),
        ).order_by(Prompt.updated_at.desc())
        
        # 构建计数查询（不包含 joinedload 等）
        count_stmt = select(func.count(Prompt.id))
        
        # 文本搜索
        if q:
            like_term = f"%{q}%"
            search_filter = (
                (Prompt.name.ilike(like_term))
                | (Prompt.author.ilike(like_term))
                | (PromptClass.name.ilike(like_term))
            )
            stmt = stmt.join(Prompt.prompt_class).where(search_filter)
            count_stmt = count_stmt.join(Prompt.prompt_class).where(search_filter)
        
        # 媒体类型筛选
        if media_type:
            stmt = stmt.where(Prompt.media_type == media_type)
            count_stmt = count_stmt.where(Prompt.media_type == media_type)
        
        # 标签筛选
        if tags:
            try:
                tag_ids = [int(tag_id.strip()) for tag_id in tags.split(',') if tag_id.strip()]
                if tag_ids:
                    # 使用 any() 进行标签筛选（包含任意一个标签即可）
                    from app.models.prompt import prompt_tag_association
                    stmt = stmt.join(prompt_tag_association).where(prompt_tag_association.c.tag_id.in_(tag_ids)).distinct()
                    count_stmt = count_stmt.join(prompt_tag_association).where(prompt_tag_association.c.tag_id.in_(tag_ids)).distinct()
            except ValueError:
                raise GalleryValidationError("标签ID格式错误")
        
        # 查询总数
        total = db.execute(count_stmt).scalar() or 0
        
        # 应用分页
        stmt = stmt.offset(offset).limit(limit)
        
        # 执行查询
        prompts = list(db.execute(stmt).unique().scalars().all())
        
        # 转换为 PromptRead
        result = [PromptRead.model_validate(prompt) for prompt in prompts]
        
        # 计算分页信息
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        current_page = (offset // limit) + 1
        
        # 转换为标准画廊响应格式
        return GalleryResponse.success(
            data=result,
            pagination={
                "page": current_page,
                "pageSize": limit,
                "total": total,
                "totalPages": total_pages
            }
        )
    except HTTPException:
        # 重新抛出HTTP异常（保持原有错误处理）
        raise
    except SQLAlchemyError as e:
        print(f"数据库错误: {e}")
        raise GalleryDatabaseError("查询提示词列表时数据库错误")
    except Exception as e:
        print(f"未知错误: {e}")
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