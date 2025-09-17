from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MetricBase(BaseModel):
    is_valid_json: bool | None = None
    schema_pass: bool | None = None
    missing_fields: dict | None = None
    type_mismatches: dict | None = None
    consistency_score: float | None = None
    numeric_accuracy: float | None = None
    boolean_accuracy: float | None = None


class MetricCreate(MetricBase):
    result_id: int


class MetricRead(MetricBase):
    id: int
    result_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
