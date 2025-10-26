from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AttachmentBase(BaseModel):
    """附件基础模式"""
    filename: str = Field(..., max_length=255, description="存储文件名")
    original_filename: str = Field(..., max_length=255, description="原始文件名")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    mime_type: str = Field(..., max_length=100, description="MIME 类型")

    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """验证文件大小限制"""
        max_size = 10 * 1024 * 1024  # 10MB
        if v > max_size:
            raise ValueError(f"文件大小不能超过 {max_size // (1024 * 1024)}MB")
        return v

    @field_validator('mime_type')
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """验证 MIME 类型格式"""
        if not v or '/' not in v:
            raise ValueError("MIME 类型格式无效")
        
        # 支持的 MIME 类型列表
        allowed_types = {
            # 图片类型
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp',
            # 文档类型
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain', 'text/csv',
            # 音频类型
            'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4',
            # 视频类型
            'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/webm'
        }
        
        if v not in allowed_types:
            raise ValueError(f"不支持的文件类型: {v}")
        
        return v


class AttachmentCreate(AttachmentBase):
    """附件创建模式"""
    prompt_id: int | None = Field(None, ge=1, description="关联的提示词 ID（可选，用于临时上传）")
    file_path: str = Field(..., max_length=500, description="文件存储路径")
    thumbnail_path: str | None = Field(None, max_length=500, description="缩略图路径")
    file_metadata: dict[str, Any] | None = Field(None, description="文件元数据")


class AttachmentRead(AttachmentBase):
    """附件读取模式"""
    id: int
    prompt_id: int | None = None  # 允许为空
    thumbnail_path: str | None = None
    file_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    download_url: str = Field(..., description="文件下载链接")
    thumbnail_url: str | None = Field(None, description="缩略图链接")

    model_config = ConfigDict(from_attributes=True)


class AttachmentUpdate(BaseModel):
    """附件更新模式"""
    filename: str | None = Field(None, max_length=255, description="存储文件名")
    file_metadata: dict[str, Any] | None = Field(None, description="文件元数据")


class AttachmentListResponse(BaseModel):
    """附件列表响应模式"""
    items: list[AttachmentRead]
    total: int = Field(..., ge=0, description="附件总数")


class AttachmentUploadResponse(BaseModel):
    """文件上传响应模式"""
    attachment: AttachmentRead
    message: str = Field(default="文件上传成功", description="响应消息")


__all__ = [
    "AttachmentBase",
    "AttachmentCreate", 
    "AttachmentRead",
    "AttachmentUpdate",
    "AttachmentListResponse",
    "AttachmentUploadResponse"
]