from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.usage import LLMUsageLog


def list_quick_test_usage_logs(
    db: Session, *, limit: int = 20, offset: int = 0
) -> list[LLMUsageLog]:
    stmt = (
        select(LLMUsageLog)
        .options(selectinload(LLMUsageLog.provider))
        .where(LLMUsageLog.source == "quick_test")
        .order_by(LLMUsageLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt))


__all__ = ["list_quick_test_usage_logs"]
