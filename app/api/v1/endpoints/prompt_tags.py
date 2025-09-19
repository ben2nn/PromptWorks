from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prompt import PromptTag
from app.schemas.prompt import PromptTagRead

router = APIRouter()


@router.get("/", response_model=list[PromptTagRead])
def list_prompt_tags(*, db: Session = Depends(get_db)) -> list[PromptTag]:
    """按名称排序返回全部 Prompt 标签列表。"""

    stmt = select(PromptTag).order_by(PromptTag.name.asc())
    return list(db.execute(stmt).scalars().all())
