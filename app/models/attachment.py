from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

if TYPE_CHECKING:
    from app.models.prompt import Prompt

from app.models.base import Base


class PromptAttachment(Base):
    """提示词附件模型
    
    用于存储与提示词关联的文件附件信息，包括：
    - 文件基本信息（名称、大小、类型）
    - 存储路径信息
    - 缩略图路径（适用于图片）
    - 文件元数据（分辨率、时长等）
    """
    __tablename__ = "prompt_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 存储分辨率、时长等信息
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # 关联关系
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="attachments")


__all__ = ["PromptAttachment"]