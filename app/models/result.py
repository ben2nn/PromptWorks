from __future__ import annotations

from datetime import datetime

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONBCompat
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.metric import Metric
    from app.models.test_run import TestRun


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    test_run_id: Mapped[int] = mapped_column(
        ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False
    )
    run_index: Mapped[int] = mapped_column(Integer, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_output: Mapped[dict | None] = mapped_column(JSONBCompat, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="results")
    metrics: Mapped[list["Metric"]] = relationship(
        "Metric",
        back_populates="result",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
