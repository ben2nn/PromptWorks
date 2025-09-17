from datetime import datetime
from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class LLMProviderBase(BaseModel):
    provider_name: str = Field(..., description="Human readable or vendor name")
    model_name: str = Field(..., description="Target model identifier")
    base_url: AnyHttpUrl | None = Field(None, description="Optional override of the API base URL")
    api_key: str = Field(..., min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    logo_url: AnyHttpUrl | None = None
    logo_emoji: str | None = Field(
        default=None,
        description="Emoji representation used when no logo URL is provided",
        max_length=16,
    )
    is_custom: bool = False


class LLMProviderCreate(LLMProviderBase):
    pass


class LLMProviderUpdate(BaseModel):
    provider_name: str | None = None
    model_name: str | None = None
    base_url: AnyHttpUrl | None = None
    api_key: str | None = None
    parameters: dict[str, Any] | None = None
    logo_url: AnyHttpUrl | None = None
    logo_emoji: str | None = Field(default=None, max_length=16)
    is_custom: bool | None = None


class LLMProviderRead(LLMProviderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
