from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PromptBase(BaseModel):
    name: str
    version: str
    content: str
    description: str | None = None
    author: str | None = None


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    content: str | None = None
    description: str | None = None
    author: str | None = None


class PromptRead(PromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
