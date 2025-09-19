from __future__ import annotations

from typing import Any, Sequence

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db.session import get_db
from app.models.llm_provider import LLMProvider
from app.schemas.llm_provider import (
    LLMProviderCreate,
    LLMProviderRead,
    LLMProviderUpdate,
)

router = APIRouter()

# 初始化接口级日志对象，方便在各个操作中手动打日志
logger = get_logger("promptworks.api.llms")

KNOWN_PROVIDER_DEFAULTS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "google": "https://generativelanguage.googleapis.com/v1beta",
}
DEFAULT_INVOKE_TIMEOUT = 30.0


class ChatMessage(BaseModel):
    role: str = Field(..., description="聊天消息的角色，例如 system、user、assistant")
    content: Any = Field(..., description="遵循 OpenAI 聊天格式的消息内容")


class LLMInvocationRequest(BaseModel):
    messages: list[ChatMessage]
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="额外的 OpenAI 兼容参数"
    )
    model: str | None = Field(default=None, description="可选的模型覆盖参数")


def _normalize_provider_name(provider_name: str) -> str:
    return provider_name.strip().lower()


def _normalize_base_url(base_url: str | AnyHttpUrl) -> str:
    normalized = str(base_url)
    return normalized.rstrip("/")


def _resolve_provider_defaults(
    *,
    provider_name: str,
    is_custom: bool | None,
    base_url: str | None,
) -> tuple[bool, str]:
    normalized = _normalize_provider_name(provider_name)
    known_default = KNOWN_PROVIDER_DEFAULTS.get(normalized)
    resolved_is_custom = is_custom if is_custom is not None else known_default is None

    if resolved_is_custom:
        if not base_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="自定义提供者必须提供基础 URL。",
            )
        return True, _normalize_base_url(base_url)

    if not base_url:
        if not known_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该提供者需要配置基础 URL。",
            )
        base_url = known_default

    return False, _normalize_base_url(base_url)


def _ensure_logo_constraints(*, is_custom: bool, logo_emoji: str | None) -> None:
    if logo_emoji and not is_custom:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅允许自定义提供者设置 logo 表情符号。",
        )


def _get_provider_or_404(db: Session, provider_id: int) -> LLMProvider:
    provider = db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到指定的提供者"
        )
    return provider


@router.get("/", response_model=list[LLMProviderRead])
def list_llms(
    *,
    db: Session = Depends(get_db),
    provider_name: str | None = Query(default=None, alias="provider"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Sequence[LLMProvider]:
    """返回分页的 LLM 提供者列表。"""

    # 记录列表查询参数，便于追踪调用来源
    logger.info(
        "查询 LLM 提供者列表: provider=%s limit=%s offset=%s",
        provider_name,
        limit,
        offset,
    )

    stmt = (
        select(LLMProvider)
        .order_by(LLMProvider.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if provider_name:
        stmt = stmt.where(LLMProvider.provider_name.ilike(f"%{provider_name}%"))

    return list(db.scalars(stmt))


@router.post("/", response_model=LLMProviderRead, status_code=status.HTTP_201_CREATED)
def create_llm(
    *,
    db: Session = Depends(get_db),
    payload: LLMProviderCreate,
) -> LLMProvider:
    """创建一个新的 LLM 提供者记录。"""

    # 使用 JSON 模式确保 URL 字段在进入 SQLAlchemy 前被序列化为字符串
    data = payload.model_dump(mode="json")
    data["parameters"] = data.get("parameters") or {}
    provider_name = data["provider_name"]
    resolved_is_custom, resolved_base_url = _resolve_provider_defaults(
        provider_name=provider_name,
        is_custom=data.get("is_custom"),
        base_url=data.get("base_url"),
    )
    data["is_custom"] = resolved_is_custom
    data["base_url"] = resolved_base_url
    _ensure_logo_constraints(
        is_custom=resolved_is_custom, logo_emoji=data.get("logo_emoji")
    )

    stmt = select(LLMProvider).where(
        LLMProvider.provider_name == provider_name,
        LLMProvider.model_name == data["model_name"],
        LLMProvider.base_url == data["base_url"],
    )
    if db.scalar(stmt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在具有相同名称、模型和基础 URL 的提供者。",
        )

    provider = LLMProvider(**data)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    # 记录成功创建的提供者信息，辅助审计
    logger.info(
        "创建 LLM 提供者成功: id=%s 名称=%s 模型=%s",
        provider.id,
        provider.provider_name,
        provider.model_name,
    )
    return provider


@router.get("/{provider_id}", response_model=LLMProviderRead)
def get_llm(*, db: Session = Depends(get_db), provider_id: int) -> LLMProvider:
    """返回单个 LLM 提供者信息。"""

    return _get_provider_or_404(db, provider_id)


@router.put("/{provider_id}", response_model=LLMProviderRead)
def update_llm(
    *,
    db: Session = Depends(get_db),
    provider_id: int,
    payload: LLMProviderUpdate,
) -> LLMProvider:
    """更新现有的 LLM 提供者。"""

    provider = _get_provider_or_404(db, provider_id)
    update_data = payload.model_dump(exclude_unset=True, mode="json")
    if "parameters" in update_data and update_data["parameters"] is None:
        update_data["parameters"] = {}

    combined_data: dict[str, Any] = {
        "provider_name": update_data.get("provider_name", provider.provider_name),
        "model_name": update_data.get("model_name", provider.model_name),
        "base_url": update_data.get("base_url", provider.base_url),
        "is_custom": update_data.get("is_custom", provider.is_custom),
    }
    resolved_is_custom, resolved_base_url = _resolve_provider_defaults(
        provider_name=combined_data["provider_name"],
        is_custom=combined_data["is_custom"],
        base_url=combined_data["base_url"],
    )
    combined_data["is_custom"] = resolved_is_custom
    combined_data["base_url"] = resolved_base_url
    _ensure_logo_constraints(
        is_custom=resolved_is_custom,
        logo_emoji=update_data.get("logo_emoji", provider.logo_emoji),
    )

    for key, value in update_data.items():
        setattr(provider, key, value)

    provider.provider_name = combined_data["provider_name"]
    provider.model_name = combined_data["model_name"]
    provider.base_url = combined_data["base_url"]
    provider.is_custom = combined_data["is_custom"]

    duplicate_stmt = select(LLMProvider).where(
        LLMProvider.id != provider.id,
        LLMProvider.provider_name == provider.provider_name,
        LLMProvider.model_name == provider.model_name,
        LLMProvider.base_url == provider.base_url,
    )
    if db.scalar(duplicate_stmt):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在具有相同名称、模型和基础 URL 的提供者。",
        )

    db.commit()
    db.refresh(provider)
    # 记录更新后的提供者信息，便于问题追溯
    logger.info(
        "更新 LLM 提供者成功: id=%s 名称=%s 模型=%s",
        provider.id,
        provider.provider_name,
        provider.model_name,
    )
    return provider


@router.delete(
    "/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_llm(*, db: Session = Depends(get_db), provider_id: int) -> Response:
    """删除指定的 LLM 提供者。"""

    provider = _get_provider_or_404(db, provider_id)
    db.delete(provider)
    db.commit()
    # 记录删除动作，避免重要资源被误删难以还原
    logger.info(
        "删除 LLM 提供者成功: id=%s 名称=%s", provider.id, provider.provider_name
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{provider_id}/invoke")
def invoke_llm(
    *,
    db: Session = Depends(get_db),
    provider_id: int,
    payload: LLMInvocationRequest,
) -> dict[str, Any]:
    """使用兼容 OpenAI Chat Completion 的方式调用目标 LLM。"""

    provider = _get_provider_or_404(db, provider_id)
    base_url = provider.base_url
    if not base_url:
        normalized = _normalize_provider_name(provider.provider_name)
        default_url = KNOWN_PROVIDER_DEFAULTS.get(normalized)
        if not default_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该提供者未配置基础 URL。",
            )
        base_url = default_url

    request_payload: dict[str, Any] = {}
    if provider.parameters:
        request_payload.update(provider.parameters)
    if payload.parameters:
        request_payload.update(payload.parameters)
    request_payload["model"] = payload.model or provider.model_name
    request_payload["messages"] = [message.model_dump() for message in payload.messages]

    headers = {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }

    url = f"{_normalize_base_url(base_url)}/chat/completions"
    # 记录调用外部接口的关键信息，方便排查调用链路
    logger.info("调用外部 LLM 接口: provider_id=%s url=%s", provider.id, url)
    logger.debug("LLM 请求参数: %s", request_payload)
    try:
        response = httpx.post(
            url, headers=headers, json=request_payload, timeout=DEFAULT_INVOKE_TIMEOUT
        )
    except httpx.HTTPError as exc:
        # 捕获网络层异常并输出错误日志，加速定位外部接口问题
        logger.error(
            "调用外部 LLM 接口出现网络异常: provider_id=%s 错误=%s", provider.id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {"message": response.text}
        # 输出外部接口的错误响应，方便快速定位异常原因
        logger.error(
            "外部 LLM 接口返回错误: provider_id=%s 状态码=%s 响应=%s",
            provider.id,
            response.status_code,
            error_payload,
        )
        raise HTTPException(status_code=response.status_code, detail=error_payload)

    # 正常响应时输出成功日志与耗时信息
    elapsed = getattr(response, "elapsed", None)
    elapsed_ms = elapsed.total_seconds() * 1000 if elapsed is not None else None
    if elapsed_ms is not None:
        logger.info(
            "外部 LLM 接口调用成功: provider_id=%s 耗时 %.2fms", provider.id, elapsed_ms
        )
    else:
        logger.info("外部 LLM 接口调用成功: provider_id=%s", provider.id)

    response_payload = response.json()
    try:
        choices = response_payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                logger.debug("LLM 响应内容前100字符: %s", content[:100])
    except AttributeError:
        pass

    return response_payload
