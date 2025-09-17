from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.test_run import TestRunStatus
from app.schemas.prompt import PromptRead
from app.schemas.result import ResultRead


class TestRunBase(BaseModel):
    model_name: str = Field(..., max_length=100)
    model_version: str | None = Field(default=None, max_length=50)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    repetitions: int = Field(default=1, ge=1, le=50)
    schema_data: dict | None = Field(
        default=None, alias="schema", serialization_alias="schema"
    )
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class TestRunCreate(TestRunBase):
    prompt_id: int


class TestRunUpdate(BaseModel):
    model_name: str | None = Field(default=None, max_length=100)
    model_version: str | None = Field(default=None, max_length=50)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    repetitions: int | None = Field(default=None, ge=1, le=50)
    schema_data: dict | None = Field(
        default=None, alias="schema", serialization_alias="schema"
    )
    notes: str | None = None
    status: TestRunStatus | None = None

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class TestRunRead(TestRunBase):
    id: int
    prompt_id: int
    status: TestRunStatus
    created_at: datetime
    updated_at: datetime
    prompt: PromptRead | None = None
    results: list[ResultRead] = []

    model_config = ConfigDict(
        from_attributes=True, populate_by_name=True, serialize_by_alias=True
    )
