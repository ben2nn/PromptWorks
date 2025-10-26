from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.models.prompt import Prompt, PromptClass, PromptTag, PromptVersion, MediaType
from app.schemas.prompt import PromptCreate, PromptRead, PromptUpdate
from app.services.attachment import attachment_service

router = APIRouter()


def _convert_prompt_to_read(prompt: Prompt) -> PromptRead:
    """将 Prompt SQLAlchemy 对象转换为 PromptRead Pydantic 对象
    
    手动转换附件列表，因为 AttachmentRead 需要额外的 URL 字段
    """
    from app.schemas.prompt import PromptRead
    from app.schemas.attachment import AttachmentRead
    
    # 转换附件列表
    attachment_reads = [
        attachment_service.to_attachment_read(att)
        for att in prompt.attachments
    ]
    
    # 使用 model_validate 从 SQLAlchemy 对象创建 Pydantic 对象
    prompt_dict = {
        "id": prompt.id,
        "name": prompt.name,
        "description": prompt.description,
        "prompt_class": prompt.prompt_class,
        "media_type": prompt.media_type,
        "current_version": prompt.current_version,
        "versions": prompt.versions,
        "tags": prompt.tags,
        "attachments": attachment_reads,  # 使用转换后的附件列表
        "created_at": prompt.created_at,
        "updated_at": prompt.updated_at,
    }
    
    return PromptRead.model_validate(prompt_dict)


def _prompt_query():
    return select(Prompt).options(
        joinedload(Prompt.prompt_class),
        joinedload(Prompt.current_version),
        selectinload(Prompt.versions),
        selectinload(Prompt.tags),
        selectinload(Prompt.attachments),
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


@router.get("", response_model=list[PromptRead])
@router.get("/", response_model=list[PromptRead])
def list_prompts(
    *,
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="根据名称、作者或分类模糊搜索"),
    media_type: MediaType | None = Query(default=None, description="按媒体类型筛选"),
    limit: int = Query(default=1000, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
) -> list[PromptRead]:
    """按更新时间倒序分页列出 Prompt，支持媒体类型筛选。"""

    stmt = (
        _prompt_query().order_by(Prompt.updated_at.desc()).offset(offset).limit(limit)
    )
    
    # 文本搜索
    if q:
        like_term = f"%{q}%"
        stmt = stmt.join(Prompt.prompt_class).where(
            (Prompt.name.ilike(like_term))
            | (Prompt.author.ilike(like_term))
            | (PromptClass.name.ilike(like_term))
        )
    
    # 媒体类型筛选
    if media_type:
        stmt = stmt.where(Prompt.media_type == media_type)

    prompts = list(db.execute(stmt).unique().scalars().all())
    
    # 转换为 PromptRead，包括附件的 URL 字段
    return [_convert_prompt_to_read(prompt) for prompt in prompts]


@router.post("", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PromptRead, status_code=status.HTTP_201_CREATED)
def create_prompt(*, db: Session = Depends(get_db), payload: PromptCreate) -> PromptRead:
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
            media_type=payload.media_type,
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
        if payload.media_type is not None:
            prompt.media_type = payload.media_type

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
        contentzh=payload.contentzh,
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

    prompt = _get_prompt_or_404(db, prompt.id)
    return _convert_prompt_to_read(prompt)


@router.get("/{prompt_id}", response_model=PromptRead)
def get_prompt(*, db: Session = Depends(get_db), prompt_id: int) -> PromptRead:
    """根据 ID 获取 Prompt 详情，包含全部版本信息和附件。"""

    prompt = _get_prompt_or_404(db, prompt_id)
    
    # 转换为 PromptRead，包括附件的 URL 字段
    return _convert_prompt_to_read(prompt)


@router.put("/{prompt_id}", response_model=PromptRead)
def update_prompt(
    *, db: Session = Depends(get_db), prompt_id: int, payload: PromptUpdate
) -> PromptRead:
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
            contentzh=payload.contentzh,
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

    prompt = _get_prompt_or_404(db, prompt_id)
    return _convert_prompt_to_read(prompt)


@router.put("/{prompt_id}/media-type", response_model=PromptRead)
def update_prompt_media_type(
    *, 
    db: Session = Depends(get_db), 
    prompt_id: int, 
    media_type: MediaType
) -> PromptRead:
    """更新提示词的媒体类型。"""

    prompt = _get_prompt_or_404(db, prompt_id)
    
    # 如果从非文本类型切换到文本类型，需要确保有内容
    if media_type == MediaType.TEXT and prompt.media_type != MediaType.TEXT:
        if not prompt.current_version or not prompt.current_version.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="切换到文本类型时必须有文本内容"
            )
    
    # 更新媒体类型
    prompt.media_type = media_type
    
    try:
        db.commit()
        db.refresh(prompt)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="更新媒体类型失败"
        ) from exc
    
    # 返回更新后的提示词（包含附件信息）
    return get_prompt(db=db, prompt_id=prompt_id)


@router.delete(
    "/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_prompt(*, db: Session = Depends(get_db), prompt_id: int) -> Response:
    """删除 Prompt 及其全部版本和附件。"""

    prompt = db.get(Prompt, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt 不存在"
        )

    # 删除关联的附件
    if prompt.media_type != MediaType.TEXT:
        attachment_service.delete_prompt_attachments(db, prompt_id)

    db.delete(prompt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
