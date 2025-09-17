from __future__ import annotations

from datetime import datetime

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONBCompat
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.result import Result


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("results.id", ondelete="CASCADE"), nullable=False
    )
    is_valid_json: Mapped[bool | None] = mapped_column(nullable=True)
    schema_pass: Mapped[bool | None] = mapped_column(nullable=True)
    missing_fields: Mapped[dict | None] = mapped_column(JSONBCompat, nullable=True)
    type_mismatches: Mapped[dict | None] = mapped_column(JSONBCompat, nullable=True)
    consistency_score: Mapped[float | None] = mapped_column(nullable=True)
    numeric_accuracy: Mapped[float | None] = mapped_column(nullable=True)
    boolean_accuracy: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    result: Mapped["Result"] = relationship("Result", back_populates="metrics")
