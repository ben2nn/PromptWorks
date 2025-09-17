from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate, PromptRead, PromptUpdate

router = APIRouter()


@router.get("/", response_model=list[PromptRead])
def list_prompts(
    *,
    db: Session = Depends(get_db),
    q: str | None = Query(
        default=None, description="Filter prompts by partial name or author."
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Sequence[Prompt]:
    """按最近更新时间返回提示词的分页列表。"""

    stmt = select(Prompt).order_by(Prompt.updated_at.desc()).offset(offset).limit(limit)
    if q:
        like_term = f"%{q}%"
        stmt = stmt.where(
            (Prompt.name.ilike(like_term)) | (Prompt.author.ilike(like_term))
        )

    return list(db.scalars(stmt))


@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(*, db: Session = Depends(get_db), payload: PromptCreate) -> Prompt:
    """创建新的提示词版本。"""

    prompt = Prompt(**payload.model_dump())
    db.add(prompt)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt with the same name and version already exists.",
        ) from exc
    db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(*, db: Session = Depends(get_db), prompt_id: int) -> Prompt:
    """根据 ID 获取单个提示词，不存在时返回 404。"""
    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )
    return prompt


@router.put("/{prompt_id}", response_model=PromptRead)
def update_prompt(
    *, db: Session = Depends(get_db), prompt_id: int, payload: PromptUpdate
) -> Prompt:
    """根据 ID 更新提示词内容，处理重复版本冲突。"""
    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(prompt, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt with the same name and version already exists.",
        ) from exc

    db.refresh(prompt)
    return prompt


@router.delete(
    "/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_prompt(*, db: Session = Depends(get_db), prompt_id: int) -> Response:
    """删除指定 ID 的提示词并返回 204。"""
    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    db.delete(prompt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
