"""附件管理服务

提供附件的完整生命周期管理，包括上传、存储、查询和删除。
"""

from typing import Any

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.attachment import PromptAttachment
from app.models.prompt import Prompt, MediaType
from app.schemas.attachment import AttachmentCreate, AttachmentRead
from app.services.file_storage import file_storage_service
from app.services.file_validation import file_validation_service
from app.services.thumbnail import thumbnail_service


class AttachmentService:
    """附件管理服务
    
    负责处理附件的上传、存储、查询和删除等操作。
    整合文件存储、验证和缩略图生成等服务。
    """
    
    def __init__(self):
        self.storage_service = file_storage_service
        self.validation_service = file_validation_service
        self.thumbnail_service = thumbnail_service
    
    async def upload_temporary_attachment(
        self,
        db: Session,
        file: UploadFile,
        media_type: MediaType | None = None
    ) -> PromptAttachment:
        """临时上传附件（不关联提示词）
        
        Args:
            db: 数据库会话
            file: 上传的文件对象
            media_type: 媒体类型（可选）
            
        Returns:
            创建的附件对象（prompt_id 为 None）
            
        Raises:
            HTTPException: 上传失败时抛出异常
        """
        # 使用默认媒体类型或指定的类型
        target_media_type = media_type or MediaType.IMAGE
        
        # 验证文件
        is_valid, error_msg, detected_mime = await self.validation_service.validate_upload_file(
            file, target_media_type
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        try:
            # 保存原始文件
            filename, file_path = await self.storage_service.save_file(file, "attachments")
            
            # 读取文件内容用于后续处理
            content = await file.read()
            await file.seek(0)  # 重置文件指针
            
            # 初始化附件数据（不关联 prompt_id）
            attachment_data = AttachmentCreate(
                prompt_id=None,  # 临时上传，不关联提示词
                filename=filename,
                original_filename=file.filename or "unknown",
                file_size=len(content),
                mime_type=detected_mime,
                file_path=file_path,
                thumbnail_path=None,
                file_metadata={}
            )
            
            # 如果是图片，生成缩略图和提取元数据
            if self.thumbnail_service.is_image_file(detected_mime):
                try:
                    thumbnail_content, thumbnail_filename, image_metadata = (
                        self.thumbnail_service.process_image(
                            content, file.filename or "unknown", detected_mime
                        )
                    )
                    
                    # 保存缩略图
                    thumbnail_path = self.storage_service.save_binary_file(
                        thumbnail_content, thumbnail_filename, "thumbnails"
                    )
                    
                    attachment_data.thumbnail_path = thumbnail_path
                    attachment_data.file_metadata = image_metadata
                    
                except Exception as e:
                    # 缩略图生成失败不影响文件上传，只记录错误
                    attachment_data.file_metadata = {
                        "thumbnail_error": f"缩略图生成失败: {str(e)}"
                    }
            
            # 保存到数据库
            db_attachment = PromptAttachment(**attachment_data.model_dump())
            db.add(db_attachment)
            db.commit()
            db.refresh(db_attachment)
            
            return db_attachment
            
        except Exception as e:
            # 如果数据库操作失败，清理已保存的文件
            if 'file_path' in locals():
                self.storage_service.delete_file(file_path)
            if 'thumbnail_path' in locals():
                self.storage_service.delete_file(thumbnail_path)
            
            db.rollback()
            raise HTTPException(
                status_code=500, 
                detail=f"附件上传失败: {str(e)}"
            ) from e

    async def upload_attachment(
        self, 
        db: Session, 
        prompt_id: int, 
        file: UploadFile,
        media_type: MediaType | None = None
    ) -> PromptAttachment:
        """上传附件到指定提示词
        
        Args:
            db: 数据库会话
            prompt_id: 提示词 ID
            file: 上传的文件对象
            media_type: 媒体类型（可选，如果不提供则从提示词获取）
            
        Returns:
            创建的附件对象
            
        Raises:
            HTTPException: 上传失败时抛出异常
        """
        # 验证提示词是否存在
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="提示词不存在")
        
        # 获取媒体类型
        target_media_type = media_type or prompt.media_type
        
        # 验证文件
        is_valid, error_msg, detected_mime = await self.validation_service.validate_upload_file(
            file, target_media_type
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        try:
            # 保存原始文件
            filename, file_path = await self.storage_service.save_file(file, "attachments")
            
            # 读取文件内容用于后续处理
            content = await file.read()
            await file.seek(0)  # 重置文件指针
            
            # 初始化附件数据
            attachment_data = AttachmentCreate(
                prompt_id=prompt_id,
                filename=filename,
                original_filename=file.filename or "unknown",
                file_size=len(content),
                mime_type=detected_mime,
                file_path=file_path,
                thumbnail_path=None,
                file_metadata={}
            )
            
            # 如果是图片，生成缩略图和提取元数据
            if self.thumbnail_service.is_image_file(detected_mime):
                try:
                    thumbnail_content, thumbnail_filename, image_metadata = (
                        self.thumbnail_service.process_image(
                            content, file.filename or "unknown", detected_mime
                        )
                    )
                    
                    # 保存缩略图
                    thumbnail_path = self.storage_service.save_binary_file(
                        thumbnail_content, thumbnail_filename, "thumbnails"
                    )
                    
                    attachment_data.thumbnail_path = thumbnail_path
                    attachment_data.file_metadata = image_metadata
                    
                except Exception as e:
                    # 缩略图生成失败不影响文件上传，只记录错误
                    attachment_data.file_metadata = {
                        "thumbnail_error": f"缩略图生成失败: {str(e)}"
                    }
            
            # 保存到数据库
            db_attachment = PromptAttachment(**attachment_data.model_dump())
            db.add(db_attachment)
            db.commit()
            db.refresh(db_attachment)
            
            return db_attachment
            
        except Exception as e:
            # 如果数据库操作失败，清理已保存的文件
            if 'file_path' in locals():
                self.storage_service.delete_file(file_path)
            if 'thumbnail_path' in locals():
                self.storage_service.delete_file(thumbnail_path)
            
            db.rollback()
            raise HTTPException(
                status_code=500, 
                detail=f"附件上传失败: {str(e)}"
            ) from e
    
    def get_attachment(self, db: Session, attachment_id: int) -> PromptAttachment | None:
        """获取单个附件信息
        
        Args:
            db: 数据库会话
            attachment_id: 附件 ID
            
        Returns:
            附件对象，如果不存在则返回 None
        """
        return db.query(PromptAttachment).filter(
            PromptAttachment.id == attachment_id
        ).first()
    
    def get_prompt_attachments(
        self, 
        db: Session, 
        prompt_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[PromptAttachment]:
        """获取提示词的附件列表
        
        Args:
            db: 数据库会话
            prompt_id: 提示词 ID
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            附件列表
        """
        return db.query(PromptAttachment).filter(
            PromptAttachment.prompt_id == prompt_id
        ).offset(skip).limit(limit).all()
    
    def count_prompt_attachments(self, db: Session, prompt_id: int) -> int:
        """统计提示词的附件数量
        
        Args:
            db: 数据库会话
            prompt_id: 提示词 ID
            
        Returns:
            附件数量
        """
        return db.query(PromptAttachment).filter(
            PromptAttachment.prompt_id == prompt_id
        ).count()
    
    def delete_attachment(self, db: Session, attachment_id: int) -> bool:
        """删除附件
        
        Args:
            db: 数据库会话
            attachment_id: 附件 ID
            
        Returns:
            删除是否成功
        """
        # 获取附件信息
        attachment = self.get_attachment(db, attachment_id)
        if not attachment:
            return False
        
        try:
            # 删除物理文件
            if attachment.file_path:
                self.storage_service.delete_file(attachment.file_path)
            
            # 删除缩略图文件
            if attachment.thumbnail_path:
                self.storage_service.delete_file(attachment.thumbnail_path)
            
            # 从数据库删除记录
            db.delete(attachment)
            db.commit()
            
            return True
            
        except Exception:
            db.rollback()
            return False
    
    def delete_prompt_attachments(self, db: Session, prompt_id: int) -> int:
        """删除提示词的所有附件
        
        Args:
            db: 数据库会话
            prompt_id: 提示词 ID
            
        Returns:
            删除的附件数量
        """
        attachments = self.get_prompt_attachments(db, prompt_id)
        deleted_count = 0
        
        for attachment in attachments:
            if self.delete_attachment(db, attachment.id):
                deleted_count += 1
        
        return deleted_count
    
    def update_attachment_metadata(
        self, 
        db: Session, 
        attachment_id: int, 
        metadata: dict[str, Any]
    ) -> PromptAttachment | None:
        """更新附件元数据
        
        Args:
            db: 数据库会话
            attachment_id: 附件 ID
            metadata: 新的元数据
            
        Returns:
            更新后的附件对象，如果不存在则返回 None
        """
        attachment = self.get_attachment(db, attachment_id)
        if not attachment:
            return None
        
        try:
            # 合并元数据
            current_metadata = attachment.file_metadata or {}
            current_metadata.update(metadata)
            
            attachment.file_metadata = current_metadata
            db.commit()
            db.refresh(attachment)
            
            return attachment
            
        except Exception:
            db.rollback()
            return None
    
    def get_attachment_download_url(self, attachment: PromptAttachment) -> str:
        """获取附件下载链接
        
        Args:
            attachment: 附件对象
            
        Returns:
            下载链接
        """
        return self.storage_service.get_file_url(attachment.file_path)
    
    def get_attachment_thumbnail_url(self, attachment: PromptAttachment) -> str | None:
        """获取附件缩略图链接
        
        Args:
            attachment: 附件对象
            
        Returns:
            缩略图链接，如果没有缩略图则返回 None
        """
        if not attachment.thumbnail_path:
            return None
        
        return self.storage_service.get_file_url(attachment.thumbnail_path)
    
    def to_attachment_read(self, attachment: PromptAttachment) -> AttachmentRead:
        """将数据库对象转换为响应模式
        
        Args:
            attachment: 附件数据库对象
            
        Returns:
            附件响应模式对象
        """
        return AttachmentRead(
            id=attachment.id,
            prompt_id=attachment.prompt_id,
            filename=attachment.filename,
            original_filename=attachment.original_filename,
            file_size=attachment.file_size,
            mime_type=attachment.mime_type,
            thumbnail_path=attachment.thumbnail_path,
            file_metadata=attachment.file_metadata,
            created_at=attachment.created_at,
            updated_at=attachment.updated_at,
            download_url=self.get_attachment_download_url(attachment),
            thumbnail_url=self.get_attachment_thumbnail_url(attachment)
        )
    
    def validate_attachment_access(
        self, 
        db: Session, 
        attachment_id: int, 
        prompt_id: int | None = None
    ) -> PromptAttachment | None:
        """验证附件访问权限
        
        Args:
            db: 数据库会话
            attachment_id: 附件 ID
            prompt_id: 提示词 ID（可选，用于额外验证）
            
        Returns:
            附件对象，如果无权限或不存在则返回 None
        """
        query = db.query(PromptAttachment).filter(
            PromptAttachment.id == attachment_id
        )
        
        if prompt_id is not None:
            query = query.filter(PromptAttachment.prompt_id == prompt_id)
        
        return query.first()
    
    def get_storage_statistics(self, db: Session) -> dict[str, Any]:
        """获取存储统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            存储统计信息
        """
        # 数据库统计
        total_attachments = db.query(PromptAttachment).count()
        
        # 按类型统计
        type_stats = {}
        for media_type in MediaType:
            if media_type == MediaType.TEXT:
                continue
            
            count = db.query(PromptAttachment).join(Prompt).filter(
                Prompt.media_type == media_type
            ).count()
            type_stats[media_type.value] = count
        
        # 文件系统统计
        storage_info = self.storage_service.get_storage_info()
        
        return {
            "total_attachments": total_attachments,
            "attachments_by_type": type_stats,
            "storage_info": storage_info
        }
    
    def attach_to_prompt(
        self,
        db: Session,
        attachment_ids: list[int],
        prompt_id: int
    ) -> list[PromptAttachment]:
        """将临时附件关联到提示词
        
        Args:
            db: 数据库会话
            attachment_ids: 附件 ID 列表
            prompt_id: 提示词 ID
            
        Returns:
            更新后的附件列表
            
        Raises:
            HTTPException: 关联失败时抛出异常
        """
        # 验证提示词是否存在
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="提示词不存在")
        
        # 获取所有附件
        attachments = db.query(PromptAttachment).filter(
            PromptAttachment.id.in_(attachment_ids)
        ).all()
        
        if len(attachments) != len(attachment_ids):
            raise HTTPException(status_code=404, detail="部分附件不存在")
        
        # 检查是否有已关联的附件
        already_attached = [att for att in attachments if att.prompt_id is not None]
        if already_attached:
            raise HTTPException(
                status_code=400, 
                detail=f"附件 {[att.id for att in already_attached]} 已关联到其他提示词"
            )
        
        try:
            # 关联附件到提示词
            for attachment in attachments:
                attachment.prompt_id = prompt_id
            
            db.commit()
            
            # 刷新所有附件
            for attachment in attachments:
                db.refresh(attachment)
            
            return attachments
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"关联附件失败: {str(e)}"
            ) from e
    
    def get_temporary_attachments(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> list[PromptAttachment]:
        """获取所有临时附件（未关联提示词的附件）
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            临时附件列表
        """
        return db.query(PromptAttachment).filter(
            PromptAttachment.prompt_id.is_(None)
        ).offset(skip).limit(limit).all()
    
    def cleanup_temporary_attachments(
        self,
        db: Session,
        older_than_hours: int = 24
    ) -> int:
        """清理过期的临时附件
        
        Args:
            db: 数据库会话
            older_than_hours: 清理多少小时前的临时附件
            
        Returns:
            清理的附件数量
        """
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # 查找过期的临时附件
        old_attachments = db.query(PromptAttachment).filter(
            PromptAttachment.prompt_id.is_(None),
            PromptAttachment.created_at < cutoff_time
        ).all()
        
        deleted_count = 0
        for attachment in old_attachments:
            if self.delete_attachment(db, attachment.id):
                deleted_count += 1
        
        return deleted_count

    def cleanup_orphaned_files(self, db: Session) -> dict[str, int]:
        """清理孤立的文件（数据库中不存在但文件系统中存在的文件）
        
        Args:
            db: 数据库会话
            
        Returns:
            清理统计信息
        """
        # 这是一个维护功能，实际实现需要遍历文件系统
        # 并与数据库记录进行比对，这里提供基本框架
        
        cleaned_files = 0
        cleaned_thumbnails = 0
        
        # TODO: 实现具体的清理逻辑
        # 1. 遍历存储目录中的所有文件
        # 2. 检查每个文件是否在数据库中有对应记录
        # 3. 删除没有对应记录的文件
        
        return {
            "cleaned_files": cleaned_files,
            "cleaned_thumbnails": cleaned_thumbnails
        }


# 创建全局实例
attachment_service = AttachmentService()


__all__ = ["AttachmentService", "attachment_service"]