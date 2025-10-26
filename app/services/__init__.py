"""服务层模块

提供应用程序的业务逻辑服务。
"""

from app.services.attachment import AttachmentService, attachment_service
from app.services.file_storage import FileStorageService, file_storage_service
from app.services.file_validation import FileValidationService, file_validation_service
from app.services.thumbnail import ThumbnailService, thumbnail_service

__all__ = [
    # 附件管理
    "AttachmentService",
    "attachment_service",
    
    # 文件存储
    "FileStorageService", 
    "file_storage_service",
    
    # 文件验证
    "FileValidationService",
    "file_validation_service",
    
    # 缩略图生成
    "ThumbnailService",
    "thumbnail_service",
]