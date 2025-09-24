from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.models.prompt import Prompt, PromptClass, PromptTag, PromptVersion
from app.schemas.prompt import PromptCreate, PromptRead, PromptUpdate

router = APIRouter()


def _prompt_query():
    return select(Prompt).options(
        joinedload(Prompt.prompt_class),
        joinedload(Prompt.current_version),
        selectinload(Prompt.versions),
        selectinload(Prompt.tags),
    )


def _get_prompt_or_404(db: Session, prompt_id: int) -> Prompt:
    stmt = _prompt_query().where(Prompt.id == prompt_id)
    prompt = db.execute(stmt).unique().scalar_one_or_none()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt 不存在"
        )
    return prompt


def _resolve_prompt_class(
    db: Session,
    *,
    class_id: int | None,
    class_name: str | None,
    class_description: str | None,
) -> PromptClass:
    if class_id is not None:
        prompt_class = db.get(PromptClass, class_id)
        if not prompt_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的 Prompt 分类不存在",
            )
        return prompt_class

    assert class_name is not None
    trimmed = class_name.strip()
    stmt = select(PromptClass).where(PromptClass.name == trimmed)
    prompt_class = db.scalar(stmt)
    if prompt_class:
        if class_description and not prompt_class.description:
            prompt_class.description = class_description
        return prompt_class

    prompt_class = PromptClass(name=trimmed, description=class_description)
    db.add(prompt_class)
    db.flush()
    return prompt_class


def _resolve_prompt_tags(db: Session, tag_ids: list[int]) -> list[PromptTag]:
    if not tag_ids:
        return []

    unique_ids = list(dict.fromkeys(tag_ids))
    stmt = select(PromptTag).where(PromptTag.id.in_(unique_ids))
    tags = db.execute(stmt).scalars().all()
    found_ids = {tag.id for tag in tags}
    missing = [tag_id for tag_id in unique_ids if tag_id not in found_ids]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"以下标签不存在: {missing}",
        )
    id_to_tag = {tag.id: tag for tag in tags}
    return [id_to_tag[tag_id] for tag_id in unique_ids]


@router.get("/", response_model=list[PromptRead])
def list_prompts(
    *,
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="根据名称、作者或分类模糊搜索"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Sequence[Prompt]:
    """按更新时间倒序分页列出 Prompt。"""

    stmt = (
        _prompt_query().order_by(Prompt.updated_at.desc()).offset(offset).limit(limit)
    )
    if q:
        like_term = f"%{q}%"
        stmt = stmt.join(Prompt.prompt_class).where(
            (Prompt.name.ilike(like_term))
            | (Prompt.author.ilike(like_term))
            | (PromptClass.name.ilike(like_term))
        )

    return list(db.execute(stmt).unique().scalars().all())


@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(*, db: Session = Depends(get_db), payload: PromptCreate) -> Prompt:
    """创建 Prompt 并写入首个版本，缺少分类时自动创建分类。"""

    prompt_class = _resolve_prompt_class(
        db,
        class_id=payload.class_id,
        class_name=payload.class_name,
        class_description=payload.class_description,
    )

    stmt = select(Prompt).where(
        Prompt.class_id == prompt_class.id, Prompt.name == payload.name
    )
    prompt = db.scalar(stmt)
    created_new_prompt = False
    if not prompt:
        prompt = Prompt(
            name=payload.name,
            description=payload.description,
            author=payload.author,
            prompt_class=prompt_class,
        )
        db.add(prompt)
        db.flush()
        created_new_prompt = True
    else:
        if payload.description is not None:
            prompt.description = payload.description
        if payload.author is not None:
            prompt.author = payload.author

    if payload.tag_ids is not None:
        prompt.tags = _resolve_prompt_tags(db, payload.tag_ids)
    elif created_new_prompt:
        prompt.tags = []

    existing_version = db.scalar(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == payload.version,
        )
    )
    if existing_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该 Prompt 已存在同名版本",
        )

    prompt_version = PromptVersion(
        prompt=prompt,
        version=payload.version,
        content=payload.content,
    )
    db.add(prompt_version)
    db.flush()
    prompt.current_version = prompt_version

    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover 数据库完整性异常回滚
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="创建 Prompt 时发生数据冲突"
        ) from exc

    return _get_prompt_or_404(db, prompt.id)


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(*, db: Session = Depends(get_db), prompt_id: int) -> Prompt:
    """根据 ID 获取 Prompt 详情，包含全部版本信息。"""

    return _get_prompt_or_404(db, prompt_id)


@router.put("/{prompt_id}", response_model=PromptRead)
def update_prompt(
    *, db: Session = Depends(get_db), prompt_id: int, payload: PromptUpdate
) -> Prompt:
    """更新 Prompt 及其元数据，可选择创建新版本或切换当前版本。"""

    prompt = _get_prompt_or_404(db, prompt_id)

    if payload.class_id is not None or (
        payload.class_name and payload.class_name.strip()
    ):
        prompt_class = _resolve_prompt_class(
            db,
            class_id=payload.class_id,
            class_name=payload.class_name,
            class_description=payload.class_description,
        )
        prompt.prompt_class = prompt_class

    if payload.name is not None:
        prompt.name = payload.name
    if payload.description is not None:
        prompt.description = payload.description
    if payload.author is not None:
        prompt.author = payload.author

    if payload.tag_ids is not None:
        prompt.tags = _resolve_prompt_tags(db, payload.tag_ids)

    if payload.version is not None and payload.content is not None:
        exists = db.scalar(
            select(PromptVersion).where(
                PromptVersion.prompt_id == prompt.id,
                PromptVersion.version == payload.version,
            )
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="同名版本已存在"
            )
        new_version = PromptVersion(
            prompt=prompt,
            version=payload.version,
            content=payload.content,
        )
        db.add(new_version)
        db.flush()
        prompt.current_version = new_version

    if payload.activate_version_id is not None:
        if payload.version is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="activate_version_id 与 version/content 不能同时出现",
            )
        target_version = db.get(PromptVersion, payload.activate_version_id)
        if not target_version or target_version.prompt_id != prompt.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目标版本不存在或不属于该 Prompt",
            )
        prompt.current_version = target_version

    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover 数据库完整性异常回滚
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="更新 Prompt 失败"
        ) from exc

    return _get_prompt_or_404(db, prompt_id)


@router.delete(
    "/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_prompt(*, db: Session = Depends(get_db), prompt_id: int) -> Response:
    """删除 Prompt 及其全部版本。"""

    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt 不存在"
        )

    db.delete(prompt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
