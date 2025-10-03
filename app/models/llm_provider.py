from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LLMProvider(Base):
    __tablename__ = "llm_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_key: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    provider_name: Mapped[str] = mapped_column(String(150), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_emoji: Mapped[str | None] = mapped_column(String(16), nullable=True)
    default_model_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    models: Mapped[list["LLMModel"]] = relationship(
        "LLMModel",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover - 调试辅助
        return (
            "LLMProvider(id={id}, provider_name={provider}, base_url={base}, models={count})"
        ).format(
            id=self.id,
            provider=self.provider_name,
            base=self.base_url,
            count=len(self.models),
        )


class LLMModel(Base):
    __tablename__ = "llm_models"
    __table_args__ = (
        UniqueConstraint("provider_id", "name", name="uq_llm_model_provider_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("llm_providers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    capability: Mapped[str | None] = mapped_column(String(120), nullable=True)
    quota: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    provider: Mapped[LLMProvider] = relationship("LLMProvider", back_populates="models")

    def __repr__(self) -> str:  # pragma: no cover - 调试辅助
        return ("LLMModel(id={id}, provider_id={provider}, name={name})").format(
            id=self.id, provider=self.provider_id, name=self.name
        )
