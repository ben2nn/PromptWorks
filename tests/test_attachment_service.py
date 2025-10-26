"""附件服务单元测试

测试附件管理服务的各个方法，包括：
- 文件上传和存储
- 附件查询和管理
- 文件验证逻辑
- 缩略图生成
- 错误处理
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.attachment import PromptAttachment
from app.models.prompt import Prompt, MediaType
from app.services.attachment import attachment_service
from app.services.file_validation import file_validation_service
from app.services.file_storage import file_storage_service


class TestAttachmentService:
    """附件服务测试类"""

    @pytest.fixture
    def sample_prompt(self, db_session: Session) -> Prompt:
        """创建测试用的提示词"""
        from app.models.prompt import PromptClass
        
        # 创建提示词分类
        prompt_class = PromptClass(
            name="测试分类",
            description="用于测试的分类"
        )
        db_session.add(prompt_class)
        db_session.commit()
        
        # 创建提示词
        prompt = Prompt(
            class_id=prompt_class.id,
            name="测试提示词",
            description="用于测试的提示词",
            media_type=MediaType.IMAGE
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt

    @pytest.fixture
    def sample_image_file(self) -> UploadFile:
        """创建测试用的图片文件"""
        # 创建一个简单的 PNG 文件头
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        content = png_header + b'\x00' * 100  # 添加一些填充数据
        
        file_obj = io.BytesIO(content)
        return UploadFile(
            filename="test_image.png",
            file=file_obj,
            size=len(content),
            headers={"content-type": "image/png"}
        )

    @pytest.fixture
    def sample_text_file(self) -> UploadFile:
        """创建测试用的文本文件"""
        content = b"This is a test document content."
        file_obj = io.BytesIO(content)
        return UploadFile(
            filename="test_document.txt",
            file=file_obj,
            size=len(content),
            headers={"content-type": "text/plain"}
        )

    async def test_upload_attachment_success(
        self, 
        db_session: Session, 
        sample_prompt: Prompt, 
        sample_image_file: UploadFile
    ):
        """测试成功上传附件"""
        with patch.object(file_storage_service, 'save_file') as mock_save_file, \
             patch.object(attachment_service.thumbnail_service, 'is_image_file') as mock_is_image, \
             patch.object(attachment_service.thumbnail_service, 'process_image') as mock_process_image, \
             patch.object(file_storage_service, 'save_binary_file') as mock_save_binary:
            
            # 设置 mock 返回值
            mock_save_file.return_value = ("unique_filename.png", "attachments/unique_filename.png")
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_unique_filename.jpg", 
                {"width": 100, "height": 100}
            )
            mock_save_binary.return_value = "thumbnails/thumb_unique_filename.jpg"
            
            # 执行上传
            attachment = await attachment_service.upload_attachment(
                db=db_session,
                prompt_id=sample_prompt.id,
                file=sample_image_file
            )
            
            # 验证结果
            assert attachment is not None
            assert attachment.prompt_id == sample_prompt.id
            assert attachment.original_filename == "test_image.png"
            assert attachment.mime_type == "image/png"
            assert attachment.file_path == "attachments/unique_filename.png"
            assert attachment.thumbnail_path == "thumbnails/thumb_unique_filename.jpg"
            assert attachment.file_metadata == {"width": 100, "height": 100}
            
            # 验证数据库中的记录
            db_attachment = db_session.query(PromptAttachment).filter(
                PromptAttachment.id == attachment.id
            ).first()
            assert db_attachment is not None
            assert db_attachment.prompt_id == sample_prompt.id

    async def test_upload_attachment_prompt_not_found(
        self, 
        db_session: Session, 
        sample_image_file: UploadFile
    ):
        """测试上传附件时提示词不存在"""
        with pytest.raises(HTTPException) as exc_info:
            await attachment_service.upload_attachment(
                db=db_session,
                prompt_id=99999,  # 不存在的提示词 ID
                file=sample_image_file
            )
        
        assert exc_info.value.status_code == 404
        assert "提示词不存在" in str(exc_info.value.detail)

    async def test_upload_attachment_validation_failure(
        self, 
        db_session: Session, 
        sample_prompt: Prompt
    ):
        """测试文件验证失败的情况"""
        # 创建一个无效的文件
        invalid_file = UploadFile(
            filename="test.exe",
            file=io.BytesIO(b"MZ\x90\x00"),  # Windows PE 文件头
            size=4
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await attachment_service.upload_attachment(
                db=db_session,
                prompt_id=sample_prompt.id,
                file=invalid_file
            )
        
        assert exc_info.value.status_code == 400

    async def test_upload_attachment_storage_failure(
        self, 
        db_session: Session, 
        sample_prompt: Prompt, 
        sample_image_file: UploadFile
    ):
        """测试文件存储失败的情况"""
        with patch.object(file_storage_service, 'save_file') as mock_save_file:
            mock_save_file.side_effect = OSError("存储失败")
            
            with pytest.raises(HTTPException) as exc_info:
                await attachment_service.upload_attachment(
                    db=db_session,
                    prompt_id=sample_prompt.id,
                    file=sample_image_file
                )
            
            assert exc_info.value.status_code == 500
            assert "附件上传失败" in str(exc_info.value.detail)

    def test_get_attachment_success(self, db_session: Session, sample_prompt: Prompt):
        """测试成功获取附件"""
        # 创建测试附件
        attachment = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png"
        )
        db_session.add(attachment)
        db_session.commit()
        db_session.refresh(attachment)
        
        # 获取附件
        result = attachment_service.get_attachment(db_session, attachment.id)
        
        assert result is not None
        assert result.id == attachment.id
        assert result.prompt_id == sample_prompt.id

    def test_get_attachment_not_found(self, db_session: Session):
        """测试获取不存在的附件"""
        result = attachment_service.get_attachment(db_session, 99999)
        assert result is None

    def test_get_prompt_attachments(self, db_session: Session, sample_prompt: Prompt):
        """测试获取提示词的附件列表"""
        # 创建多个测试附件
        attachments = []
        for i in range(3):
            attachment = PromptAttachment(
                prompt_id=sample_prompt.id,
                filename=f"test_file_{i}.png",
                original_filename=f"original_test_{i}.png",
                file_size=1024 + i,
                mime_type="image/png",
                file_path=f"attachments/test_file_{i}.png"
            )
            attachments.append(attachment)
            db_session.add(attachment)
        
        db_session.commit()
        
        # 获取附件列表
        result = attachment_service.get_prompt_attachments(db_session, sample_prompt.id)
        
        assert len(result) == 3
        assert all(att.prompt_id == sample_prompt.id for att in result)

    def test_get_prompt_attachments_with_pagination(
        self, 
        db_session: Session, 
        sample_prompt: Prompt
    ):
        """测试分页获取附件列表"""
        # 创建 5 个测试附件
        for i in range(5):
            attachment = PromptAttachment(
                prompt_id=sample_prompt.id,
                filename=f"test_file_{i}.png",
                original_filename=f"original_test_{i}.png",
                file_size=1024 + i,
                mime_type="image/png",
                file_path=f"attachments/test_file_{i}.png"
            )
            db_session.add(attachment)
        
        db_session.commit()
        
        # 测试分页
        result = attachment_service.get_prompt_attachments(
            db_session, sample_prompt.id, skip=1, limit=2
        )
        
        assert len(result) == 2

    def test_count_prompt_attachments(self, db_session: Session, sample_prompt: Prompt):
        """测试统计提示词附件数量"""
        # 创建测试附件
        for i in range(3):
            attachment = PromptAttachment(
                prompt_id=sample_prompt.id,
                filename=f"test_file_{i}.png",
                original_filename=f"original_test_{i}.png",
                file_size=1024,
                mime_type="image/png",
                file_path=f"attachments/test_file_{i}.png"
            )
            db_session.add(attachment)
        
        db_session.commit()
        
        # 统计数量
        count = attachment_service.count_prompt_attachments(db_session, sample_prompt.id)
        assert count == 3

    def test_delete_attachment_success(self, db_session: Session, sample_prompt: Prompt):
        """测试成功删除附件"""
        # 创建测试附件
        attachment = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png",
            thumbnail_path="thumbnails/test_thumb.jpg"
        )
        db_session.add(attachment)
        db_session.commit()
        attachment_id = attachment.id
        
        with patch.object(file_storage_service, 'delete_file') as mock_delete:
            mock_delete.return_value = True
            
            # 删除附件
            result = attachment_service.delete_attachment(db_session, attachment_id)
            
            assert result is True
            
            # 验证文件删除调用
            assert mock_delete.call_count == 2  # 原文件和缩略图
            
            # 验证数据库记录已删除
            db_attachment = db_session.query(PromptAttachment).filter(
                PromptAttachment.id == attachment_id
            ).first()
            assert db_attachment is None

    def test_delete_attachment_not_found(self, db_session: Session):
        """测试删除不存在的附件"""
        result = attachment_service.delete_attachment(db_session, 99999)
        assert result is False

    def test_delete_prompt_attachments(self, db_session: Session, sample_prompt: Prompt):
        """测试删除提示词的所有附件"""
        # 创建多个测试附件
        attachment_ids = []
        for i in range(3):
            attachment = PromptAttachment(
                prompt_id=sample_prompt.id,
                filename=f"test_file_{i}.png",
                original_filename=f"original_test_{i}.png",
                file_size=1024,
                mime_type="image/png",
                file_path=f"attachments/test_file_{i}.png"
            )
            db_session.add(attachment)
            db_session.commit()
            attachment_ids.append(attachment.id)
        
        with patch.object(file_storage_service, 'delete_file') as mock_delete:
            mock_delete.return_value = True
            
            # 删除所有附件
            deleted_count = attachment_service.delete_prompt_attachments(
                db_session, sample_prompt.id
            )
            
            assert deleted_count == 3
            
            # 验证数据库记录已删除
            remaining_count = attachment_service.count_prompt_attachments(
                db_session, sample_prompt.id
            )
            assert remaining_count == 0

    def test_update_attachment_metadata(self, db_session: Session, sample_prompt: Prompt):
        """测试更新附件元数据"""
        # 创建测试附件
        attachment = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png",
            file_metadata={"width": 100, "height": 100}
        )
        db_session.add(attachment)
        db_session.commit()
        
        # 更新元数据
        new_metadata = {"description": "测试图片", "tags": ["test", "image"]}
        result = attachment_service.update_attachment_metadata(
            db_session, attachment.id, new_metadata
        )
        
        assert result is not None
        assert result.file_metadata["width"] == 100  # 原有数据保留
        assert result.file_metadata["description"] == "测试图片"  # 新数据添加
        assert result.file_metadata["tags"] == ["test", "image"]

    def test_get_attachment_download_url(self, sample_prompt: Prompt):
        """测试获取附件下载链接"""
        attachment = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png"
        )
        
        with patch.object(file_storage_service, 'get_file_url') as mock_get_url:
            mock_get_url.return_value = "http://localhost/api/v1/files/attachments/test_file.png"
            
            url = attachment_service.get_attachment_download_url(attachment)
            
            assert url == "http://localhost/api/v1/files/attachments/test_file.png"
            mock_get_url.assert_called_once_with("attachments/test_file.png")

    def test_get_attachment_thumbnail_url(self, sample_prompt: Prompt):
        """测试获取附件缩略图链接"""
        # 有缩略图的附件
        attachment_with_thumb = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png",
            thumbnail_path="thumbnails/test_thumb.jpg"
        )
        
        with patch.object(file_storage_service, 'get_file_url') as mock_get_url:
            mock_get_url.return_value = "http://localhost/api/v1/files/thumbnails/test_thumb.jpg"
            
            url = attachment_service.get_attachment_thumbnail_url(attachment_with_thumb)
            
            assert url == "http://localhost/api/v1/files/thumbnails/test_thumb.jpg"
        
        # 没有缩略图的附件
        attachment_no_thumb = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.txt",
            original_filename="original_test.txt",
            file_size=1024,
            mime_type="text/plain",
            file_path="attachments/test_file.txt",
            thumbnail_path=None
        )
        
        url = attachment_service.get_attachment_thumbnail_url(attachment_no_thumb)
        assert url is None

    def test_to_attachment_read(self, sample_prompt: Prompt):
        """测试转换为响应模式"""
        attachment = PromptAttachment(
            id=1,
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png",
            thumbnail_path="thumbnails/test_thumb.jpg",
            file_metadata={"width": 100, "height": 100}
        )
        
        with patch.object(attachment_service, 'get_attachment_download_url') as mock_download_url, \
             patch.object(attachment_service, 'get_attachment_thumbnail_url') as mock_thumb_url:
            
            mock_download_url.return_value = "http://localhost/download/1"
            mock_thumb_url.return_value = "http://localhost/thumbnail/1"
            
            result = attachment_service.to_attachment_read(attachment)
            
            assert result.id == 1
            assert result.prompt_id == sample_prompt.id
            assert result.filename == "test_file.png"
            assert result.download_url == "http://localhost/download/1"
            assert result.thumbnail_url == "http://localhost/thumbnail/1"

    def test_validate_attachment_access(self, db_session: Session, sample_prompt: Prompt):
        """测试验证附件访问权限"""
        # 创建测试附件
        attachment = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png"
        )
        db_session.add(attachment)
        db_session.commit()
        
        # 测试有效访问
        result = attachment_service.validate_attachment_access(
            db_session, attachment.id, sample_prompt.id
        )
        assert result is not None
        assert result.id == attachment.id
        
        # 测试无效的提示词 ID
        result = attachment_service.validate_attachment_access(
            db_session, attachment.id, 99999
        )
        assert result is None
        
        # 测试不提供提示词 ID
        result = attachment_service.validate_attachment_access(
            db_session, attachment.id
        )
        assert result is not None

    def test_get_storage_statistics(self, db_session: Session, sample_prompt: Prompt):
        """测试获取存储统计信息"""
        # 创建不同类型的提示词和附件
        image_prompt = sample_prompt  # 已经是 IMAGE 类型
        
        from app.models.prompt import PromptClass
        
        # 创建文档分类
        doc_class = PromptClass(
            name="文档分类",
            description="文档类型分类"
        )
        db_session.add(doc_class)
        db_session.commit()
        
        doc_prompt = Prompt(
            class_id=doc_class.id,
            name="文档提示词",
            description="文档类型提示词",
            media_type=MediaType.DOCUMENT
        )
        db_session.add(doc_prompt)
        db_session.commit()
        
        # 创建附件
        for prompt in [image_prompt, doc_prompt]:
            attachment = PromptAttachment(
                prompt_id=prompt.id,
                filename="test_file.png",
                original_filename="original_test.png",
                file_size=1024,
                mime_type="image/png",
                file_path="attachments/test_file.png"
            )
            db_session.add(attachment)
        
        db_session.commit()
        
        with patch.object(file_storage_service, 'get_storage_info') as mock_storage_info:
            mock_storage_info.return_value = {
                "storage_type": "local",
                "total_size": 2048,
                "file_count": 2
            }
            
            stats = attachment_service.get_storage_statistics(db_session)
            
            assert stats["total_attachments"] == 2
            assert "attachments_by_type" in stats
            assert stats["attachments_by_type"]["image"] == 1
            assert stats["attachments_by_type"]["document"] == 1
            assert stats["storage_info"]["total_size"] == 2048


class TestFileValidationService:
    """文件验证服务测试类"""

    def test_validate_file_size_valid(self):
        """测试有效文件大小验证"""
        is_valid, error = file_validation_service.validate_file_size(1024)
        assert is_valid is True
        assert error is None

    def test_validate_file_size_too_large(self):
        """测试文件大小超限"""
        large_size = 20 * 1024 * 1024  # 20MB
        is_valid, error = file_validation_service.validate_file_size(large_size)
        assert is_valid is False
        assert "文件大小超过限制" in error

    def test_validate_file_size_invalid(self):
        """测试无效文件大小"""
        is_valid, error = file_validation_service.validate_file_size(0)
        assert is_valid is False
        assert "文件大小无效" in error

    def test_detect_mime_type_by_filename(self):
        """测试通过文件名检测 MIME 类型"""
        mime_type = file_validation_service.detect_mime_type("test.jpg")
        assert mime_type == "image/jpeg"
        
        mime_type = file_validation_service.detect_mime_type("test.png")
        assert mime_type == "image/png"
        
        mime_type = file_validation_service.detect_mime_type("test.pdf")
        assert mime_type == "application/pdf"

    def test_detect_mime_type_by_content(self):
        """测试通过文件内容检测 MIME 类型"""
        # PNG 文件头
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 20
        mime_type = file_validation_service.detect_mime_type("test.png", png_content)
        assert mime_type == "image/png"
        
        # JPEG 文件头
        jpeg_content = b'\xFF\xD8\xFF' + b'\x00' * 20
        mime_type = file_validation_service.detect_mime_type("test.jpg", jpeg_content)
        assert mime_type == "image/jpeg"

    def test_validate_mime_type_valid(self):
        """测试有效 MIME 类型验证"""
        is_valid, error = file_validation_service.validate_mime_type(
            "image/png", MediaType.IMAGE
        )
        assert is_valid is True
        assert error is None

    def test_validate_mime_type_invalid(self):
        """测试无效 MIME 类型验证"""
        is_valid, error = file_validation_service.validate_mime_type(
            "application/pdf", MediaType.IMAGE
        )
        assert is_valid is False
        assert "不支持" in error

    def test_validate_mime_type_text_media_type(self):
        """测试文本媒体类型不支持文件上传"""
        is_valid, error = file_validation_service.validate_mime_type(
            "text/plain", MediaType.TEXT
        )
        assert is_valid is False
        assert "文本类型不支持文件上传" in error

    def test_validate_file_security_safe_filename(self):
        """测试安全文件名验证"""
        is_safe, error = file_validation_service.validate_file_security(
            b"safe content", "safe_filename.jpg"
        )
        assert is_safe is True
        assert error is None

    def test_validate_file_security_unsafe_filename(self):
        """测试不安全文件名验证"""
        is_safe, error = file_validation_service.validate_file_security(
            b"content", "../unsafe.jpg"
        )
        assert is_safe is False
        assert "不安全字符" in error

    def test_validate_file_security_executable_content(self):
        """测试可执行文件内容验证"""
        # Windows PE 文件头
        pe_content = b'MZ' + b'\x00' * 100
        is_safe, error = file_validation_service.validate_file_security(
            pe_content, "test.exe"
        )
        assert is_safe is False
        assert "恶意代码" in error

    async def test_validate_upload_file_success(self):
        """测试成功验证上传文件"""
        # 创建有效的 PNG 文件
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file_obj = io.BytesIO(png_content)
        upload_file = UploadFile(
            filename="test.png",
            file=file_obj,
            size=len(png_content)
        )
        
        is_valid, error, mime_type = await file_validation_service.validate_upload_file(
            upload_file, MediaType.IMAGE
        )
        
        assert is_valid is True
        assert error is None
        assert mime_type == "image/png"

    async def test_validate_upload_file_no_filename(self):
        """测试没有文件名的上传文件"""
        file_obj = io.BytesIO(b"content")
        upload_file = UploadFile(file=file_obj)
        
        is_valid, error, mime_type = await file_validation_service.validate_upload_file(
            upload_file, MediaType.IMAGE
        )
        
        assert is_valid is False
        assert "文件名不能为空" in error
        assert mime_type is None

    def test_get_supported_extensions(self):
        """测试获取支持的文件扩展名"""
        extensions = file_validation_service.get_supported_extensions(MediaType.IMAGE)
        assert ".jpg" in extensions or ".jpeg" in extensions
        assert ".png" in extensions

    def test_format_file_size(self):
        """测试文件大小格式化"""
        assert file_validation_service.format_file_size(512) == "512 B"
        assert file_validation_service.format_file_size(1536) == "1.5 KB"
        assert file_validation_service.format_file_size(2 * 1024 * 1024) == "2.0 MB"