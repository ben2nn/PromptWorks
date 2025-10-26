from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prompt import Prompt, PromptClass
from app.schemas import (
    PromptClassCreate,
    PromptClassRead,
    PromptClassStats,
    PromptClassUpdate,
)

router = APIRouter()


@router.get("", response_model=list[PromptClassStats])
@router.get("/", response_model=list[PromptClassStats])
def list_prompt_classes(
    *,
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="按名称模糊搜索分类"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[PromptClassStats]:
    """按名称排序列出 Prompt 分类，并附带使用统计信息"""

    prompt_count = func.count(Prompt.id)
    latest_updated = func.max(Prompt.updated_at)

    stmt = (
        select(
            PromptClass,
            prompt_count.label("prompt_count"),
            latest_updated.label("latest_prompt_updated_at"),
        )
        .outerjoin(Prompt, Prompt.class_id == PromptClass.id)
        .group_by(PromptClass.id)
        .order_by(PromptClass.name.asc())
    )

    if q:
        term = q.strip()
        if term:
            stmt = stmt.where(PromptClass.name.ilike(f"%{term}%"))

    stmt = stmt.offset(offset).limit(limit)

    rows = db.execute(stmt).all()
    return [
        PromptClassStats(
            id=row.PromptClass.id,
            name=row.PromptClass.name,
            description=row.PromptClass.description,
            created_at=row.PromptClass.created_at,
            updated_at=row.PromptClass.updated_at,
            prompt_count=row.prompt_count or 0,
            latest_prompt_updated_at=row.latest_prompt_updated_at,
        )
        for row in rows
    ]


@router.post("", response_model=PromptClassRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PromptClassRead, status_code=status.HTTP_201_CREATED)
def create_prompt_class(
    *, db: Session = Depends(get_db), payload: PromptClassCreate
) -> PromptClass:
    """创建新的 Prompt 分类"""

    prompt_class = PromptClass(name=payload.name, description=payload.description)
    db.add(prompt_class)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="同名分类已存在"
        ) from exc
    db.refresh(prompt_class)
    return prompt_class


@router.patch("/{class_id}", response_model=PromptClassRead)
def update_prompt_class(
    *, db: Session = Depends(get_db), class_id: int, payload: PromptClassUpdate
) -> PromptClass:
    """更新指定 Prompt 分类"""

    prompt_class = db.get(PromptClass, class_id)
    if not prompt_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return prompt_class

    name = update_data.get("name")
    if name is not None:
        prompt_class.name = name.strip()
    if "description" in update_data:
        prompt_class.description = update_data["description"]

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="同名分类已存在"
        ) from exc
    db.refresh(prompt_class)
    return prompt_class


@router.delete(
    "/{class_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_prompt_class(*, db: Session = Depends(get_db), class_id: int) -> Response:
    """删除指定 Prompt 分类，同时清理其下所有 Prompt。"""

    prompt_class = db.get(PromptClass, class_id)
    if not prompt_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在")

    db.delete(prompt_class)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
