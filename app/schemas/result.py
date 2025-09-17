from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.metric import MetricRead


class ResultBase(BaseModel):
    run_index: int = Field(ge=0)
    output: str
    parsed_output: dict | None = None
    tokens_used: int | None = Field(default=None, ge=0)
    latency_ms: int | None = Field(default=None, ge=0)


class ResultCreate(ResultBase):
    test_run_id: int


class ResultRead(ResultBase):
    id: int
    test_run_id: int
    created_at: datetime
    metrics: list[MetricRead] = []

    model_config = ConfigDict(from_attributes=True)
