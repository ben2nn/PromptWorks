from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as PgEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TestRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    temperature: Mapped[float] = mapped_column(nullable=False, default=0.7)
    top_p: Mapped[float] = mapped_column(nullable=False, default=1.0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[TestRunStatus] = mapped_column(
        PgEnum(TestRunStatus, name="test_run_status"),
        nullable=False,
        default=TestRunStatus.PENDING,
        server_default=TestRunStatus.PENDING.value,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="test_runs")
    results: Mapped[list["Result"]] = relationship(
        "Result", back_populates="test_run", cascade="all, delete-orphan", passive_deletes=True
    )
