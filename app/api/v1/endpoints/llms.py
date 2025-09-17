from __future__ import annotations

from typing import Any, Sequence

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.llm_provider import LLMProvider
from app.schemas.llm_provider import LLMProviderCreate, LLMProviderRead, LLMProviderUpdate

router = APIRouter()

KNOWN_PROVIDER_DEFAULTS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "google": "https://generativelanguage.googleapis.com/v1beta",
}
DEFAULT_INVOKE_TIMEOUT = 30.0


class ChatMessage(BaseModel):
    role: str = Field(..., description="Chat message role such as system, user, assistant")
    content: Any = Field(..., description="Message content that follows the OpenAI chat schema")


class LLMInvocationRequest(BaseModel):
    messages: list[ChatMessage]
    parameters: dict[str, Any] = Field(default_factory=dict, description="Additional OpenAI compatible parameters")
    model: str | None = Field(default=None, description="Optional model override for this invocation")


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
                detail="Base URL is required for custom providers.",
            )
        return True, _normalize_base_url(base_url)

    if not base_url:
        if not known_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base URL is required for this provider.",
            )
        base_url = known_default

    return False, _normalize_base_url(base_url)


def _ensure_logo_constraints(*, is_custom: bool, logo_emoji: str | None) -> None:
    if logo_emoji and not is_custom:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logo emoji is only allowed for custom providers.",
        )


def _get_provider_or_404(db: Session, provider_id: int) -> LLMProvider:
    provider = db.get(LLMProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return provider


@router.get("/", response_model=list[LLMProviderRead])
def list_llms(
    *,
    db: Session = Depends(get_db),
    provider_name: str | None = Query(default=None, alias="provider"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Sequence[LLMProvider]:
    """Return a paginated list of LLM providers."""

    stmt = select(LLMProvider).order_by(LLMProvider.updated_at.desc()).offset(offset).limit(limit)
    if provider_name:
        stmt = stmt.where(LLMProvider.provider_name.ilike(f"%{provider_name}%"))

    return list(db.scalars(stmt))


@router.post("/", response_model=LLMProviderRead, status_code=status.HTTP_201_CREATED)
def create_llm(
    *,
    db: Session = Depends(get_db),
    payload: LLMProviderCreate,
) -> LLMProvider:
    """Create a new LLM provider entry."""

    data = payload.model_dump()
    data["parameters"] = data.get("parameters") or {}
    provider_name = data["provider_name"]
    resolved_is_custom, resolved_base_url = _resolve_provider_defaults(
        provider_name=provider_name,
        is_custom=data.get("is_custom"),
        base_url=data.get("base_url"),
    )
    data["is_custom"] = resolved_is_custom
    data["base_url"] = resolved_base_url
    _ensure_logo_constraints(is_custom=resolved_is_custom, logo_emoji=data.get("logo_emoji"))

    stmt = select(LLMProvider).where(
        LLMProvider.provider_name == provider_name,
        LLMProvider.model_name == data["model_name"],
        LLMProvider.base_url == data["base_url"],
    )
    if db.scalar(stmt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider with the same name, model, and base URL already exists.",
        )

    provider = LLMProvider(**data)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=LLMProviderRead)
def get_llm(*, db: Session = Depends(get_db), provider_id: int) -> LLMProvider:
    """Return a single LLM provider."""

    return _get_provider_or_404(db, provider_id)


@router.put("/{provider_id}", response_model=LLMProviderRead)
def update_llm(
    *,
    db: Session = Depends(get_db),
    provider_id: int,
    payload: LLMProviderUpdate,
) -> LLMProvider:
    """Update an existing LLM provider."""

    provider = _get_provider_or_404(db, provider_id)
    update_data = payload.model_dump(exclude_unset=True)
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
            detail="Provider with the same name, model, and base URL already exists.",
        )

    db.commit()
    db.refresh(provider)
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_llm(*, db: Session = Depends(get_db), provider_id: int) -> Response:
    """Delete an LLM provider."""

    provider = _get_provider_or_404(db, provider_id)
    db.delete(provider)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{provider_id}/invoke")
def invoke_llm(
    *,
    db: Session = Depends(get_db),
    provider_id: int,
    payload: LLMInvocationRequest,
) -> dict[str, Any]:
    """Invoke the target LLM using an OpenAI compatible chat completion call."""

    provider = _get_provider_or_404(db, provider_id)
    base_url = provider.base_url
    if not base_url:
        normalized = _normalize_provider_name(provider.provider_name)
        default_url = KNOWN_PROVIDER_DEFAULTS.get(normalized)
        if not default_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base URL is not configured for this provider.",
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
    try:
        response = httpx.post(url, headers=headers, json=request_payload, timeout=DEFAULT_INVOKE_TIMEOUT)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if response.status_code >= 400:
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {"message": response.text}
        raise HTTPException(status_code=response.status_code, detail=error_payload)

    return response.json()
