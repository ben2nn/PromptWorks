"""媒体类型和附件功能集成测试

测试完整的文件上传流程、附件管理功能和媒体类型切换，验证：
- 完整的文件上传流程（需求 1.4, 2.4, 3.2）
- 附件管理功能的端到端测试
- 媒体类型切换和相关功能
- 前后端集成的完整性
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attachment import PromptAttachment
from app.models.prompt import Prompt, MediaType
from app.services.file_storage import file_storage_service


class TestMediaTypeIntegration:
    """媒体类型集成测试类"""

    @pytest.fixture
    def sample_prompt_class(self, db_session: Session):
        """创建测试用的提示词分类"""
        from app.models.prompt import PromptClass
        
        prompt_class = PromptClass(
            name="集成测试分类",
            description="用于集成测试的分类"
        )
        db_session.add(prompt_class)
        db_session.commit()
        db_session.refresh(prompt_class)
        return prompt_class

    @pytest.fixture
    def text_prompt(self, db_session: Session, sample_prompt_class):
        """创建文本类型提示词"""
        prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="文本提示词",
            description="文本类型的提示词",
            media_type=MediaType.TEXT
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt

    @pytest.fixture
    def image_prompt(self, db_session: Session, sample_prompt_class):
        """创建图片类型提示词"""
        prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="图片提示词",
            description="图片类型的提示词",
            media_type=MediaType.IMAGE
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt

    def test_complete_file_upload_workflow(
        self, 
        client: TestClient, 
        db_session: Session,
        image_prompt: Prompt
    ):
        """测试完整的文件上传流程 - 需求 1.4, 2.4"""
        # 创建测试图片文件
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03'
        png_content += b'\x00' * 1000  # 添加更多内容使其看起来像真实图片
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
             patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
             patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
             patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
            
            # 设置 mock 返回值
            mock_save_file.return_value = ("unique_test_image.png", "attachments/unique_test_image.png")
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_unique_test_image.jpg", 
                {"width": 100, "height": 100}
            )
            mock_save_binary.return_value = "thumbnails/thumb_unique_test_image.jpg"
            
            # 步骤 1: 上传文件
            upload_response = client.post(
                f"/api/v1/prompts/{image_prompt.id}/attachments",
                files={"file": ("test_image.png", png_content, "image/png")}
            )
            
            assert upload_response.status_code == status.HTTP_201_CREATED
            upload_data = upload_response.json()
            attachment_id = upload_data["attachment"]["id"]
            
            # 验证上传响应
            assert upload_data["message"] == "文件上传成功"
            assert upload_data["attachment"]["original_filename"] == "test_image.png"
            assert upload_data["attachment"]["mime_type"] == "image/png"
            assert upload_data["attachment"]["prompt_id"] == image_prompt.id
            assert upload_data["attachment"]["file_metadata"]["width"] == 100
            assert upload_data["attachment"]["file_metadata"]["height"] == 100
            
            # 步骤 2: 验证数据库中的记录
            db_attachment = db_session.query(PromptAttachment).filter(
                PromptAttachment.id == attachment_id
            ).first()
            assert db_attachment is not None
            assert db_attachment.prompt_id == image_prompt.id
            assert db_attachment.original_filename == "test_image.png"
            assert db_attachment.thumbnail_path == "thumbnails/thumb_unique_test_image.jpg"
            
            # 步骤 3: 获取附件列表
            list_response = client.get(f"/api/v1/prompts/{image_prompt.id}/attachments")
            assert list_response.status_code == status.HTTP_200_OK
            
            list_data = list_response.json()
            assert list_data["total"] == 1
            assert len(list_data["items"]) == 1
            assert list_data["items"][0]["id"] == attachment_id
            
            # 步骤 4: 获取单个附件信息
            get_response = client.get(f"/api/v1/attachments/{attachment_id}")
            assert get_response.status_code == status.HTTP_200_OK
            
            get_data = get_response.json()
            assert get_data["id"] == attachment_id
            assert get_data["filename"] == "unique_test_image.png"
            assert get_data["original_filename"] == "test_image.png"

    def test_attachment_management_workflow(
        self, 
        client: TestClient, 
        db_session: Session,
        image_prompt: Prompt
    ):
        """测试附件管理功能的完整流程 - 需求 3.2"""
        # 创建多个测试附件
        attachments_data = [
            ("image1.jpg", "image/jpeg", b'\xFF\xD8\xFF' + b'\x00' * 500),
            ("image2.png", "image/png", b'\x89PNG\r\n\x1a\n' + b'\x00' * 500),
            ("document.pdf", "application/pdf", b'%PDF-1.4' + b'\x00' * 500)
        ]
        
        uploaded_attachments = []
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
             patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
             patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
             patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
            
            # 设置 mock 返回值
            def mock_save_file_side_effect(file, subdir):
                filename = f"unique_{file.filename}"
                return filename, f"{subdir}/{filename}"
            
            mock_save_file.side_effect = mock_save_file_side_effect
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_unique.jpg", 
                {"width": 200, "height": 150}
            )
            mock_save_binary.return_value = "thumbnails/thumb_unique.jpg"
            
            # 步骤 1: 批量上传附件
            for filename, mime_type, content in attachments_data:
                response = client.post(
                    f"/api/v1/prompts/{image_prompt.id}/attachments",
                    files={"file": (filename, content, mime_type)}
                )
                assert response.status_code == status.HTTP_201_CREATED
                uploaded_attachments.append(response.json()["attachment"])
            
            # 步骤 2: 验证附件列表
            list_response = client.get(f"/api/v1/prompts/{image_prompt.id}/attachments")
            assert list_response.status_code == status.HTTP_200_OK
            
            list_data = list_response.json()
            assert list_data["total"] == 3
            assert len(list_data["items"]) == 3
            
            # 步骤 3: 测试分页功能
            paginated_response = client.get(
                f"/api/v1/prompts/{image_prompt.id}/attachments?skip=1&limit=2"
            )
            assert paginated_response.status_code == status.HTTP_200_OK
            
            paginated_data = paginated_response.json()
            assert paginated_data["total"] == 3
            assert len(paginated_data["items"]) == 2
            
            # 步骤 4: 更新附件元数据
            first_attachment_id = uploaded_attachments[0]["id"]
            update_data = {
                "filename": "updated_image1.jpg",
                "file_metadata": {"description": "更新的图片描述", "tags": ["test", "updated"]}
            }
            
            update_response = client.put(
                f"/api/v1/attachments/{first_attachment_id}",
                json=update_data
            )
            assert update_response.status_code == status.HTTP_200_OK
            
            update_result = update_response.json()
            assert update_result["filename"] == "updated_image1.jpg"
            assert update_result["file_metadata"]["description"] == "更新的图片描述"
            
            # 步骤 5: 删除单个附件
            delete_response = client.delete(f"/api/v1/attachments/{first_attachment_id}")
            assert delete_response.status_code == status.HTTP_204_NO_CONTENT
            
            # 验证删除后的列表
            after_delete_response = client.get(f"/api/v1/prompts/{image_prompt.id}/attachments")
            after_delete_data = after_delete_response.json()
            assert after_delete_data["total"] == 2
            
            # 步骤 6: 批量删除剩余附件
            batch_delete_response = client.delete(f"/api/v1/prompts/{image_prompt.id}/attachments")
            assert batch_delete_response.status_code == status.HTTP_204_NO_CONTENT
            assert batch_delete_response.headers["X-Deleted-Count"] == "2"
            
            # 验证全部删除后的列表
            final_list_response = client.get(f"/api/v1/prompts/{image_prompt.id}/attachments")
            final_list_data = final_list_response.json()
            assert final_list_data["total"] == 0

    def test_media_type_switching_workflow(
        self, 
        client: TestClient, 
        db_session: Session,
        text_prompt: Prompt
    ):
        """测试媒体类型切换的完整流程 - 需求 1.4"""
        # 步骤 1: 验证初始状态（文本类型）
        get_response = client.get(f"/api/v1/prompts/{text_prompt.id}")
        assert get_response.status_code == status.HTTP_200_OK
        
        prompt_data = get_response.json()
        assert prompt_data["media_type"] == MediaType.TEXT.value
        
        # 步骤 2: 切换到图片类型
        update_data = {
            "media_type": MediaType.IMAGE.value
        }
        
        update_response = client.put(
            f"/api/v1/prompts/{text_prompt.id}",
            json=update_data
        )
        assert update_response.status_code == status.HTTP_200_OK
        
        updated_data = update_response.json()
        assert updated_data["media_type"] == MediaType.IMAGE.value
        
        # 步骤 3: 验证数据库中的更新
        db_session.refresh(text_prompt)
        assert text_prompt.media_type == MediaType.IMAGE
        
        # 步骤 4: 为图片类型上传附件
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 500
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
             patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
             patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
             patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
            
            mock_save_file.return_value = ("switched_image.png", "attachments/switched_image.png")
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_switched_image.jpg", 
                {"width": 300, "height": 200}
            )
            mock_save_binary.return_value = "thumbnails/thumb_switched_image.jpg"
            
            upload_response = client.post(
                f"/api/v1/prompts/{text_prompt.id}/attachments",
                files={"file": ("switched_image.png", png_content, "image/png")}
            )
            assert upload_response.status_code == status.HTTP_201_CREATED
        
        # 步骤 5: 验证附件上传成功
        attachments_response = client.get(f"/api/v1/prompts/{text_prompt.id}/attachments")
        attachments_data = attachments_response.json()
        assert attachments_data["total"] == 1
        
        # 步骤 6: 切换到文档类型
        update_to_doc = {
            "media_type": MediaType.DOCUMENT.value
        }
        
        doc_update_response = client.put(
            f"/api/v1/prompts/{text_prompt.id}",
            json=update_to_doc
        )
        assert doc_update_response.status_code == status.HTTP_200_OK
        
        # 步骤 7: 验证媒体类型统计
        stats_response = client.get("/api/v1/media-types/statistics")
        assert stats_response.status_code == status.HTTP_200_OK
        
        stats_data = stats_response.json()
        assert stats_data["total_prompts"] >= 2  # 至少有我们创建的两个提示词
        assert "by_media_type" in stats_data

    def test_file_download_and_thumbnail_workflow(
        self, 
        client: TestClient, 
        db_session: Session,
        image_prompt: Prompt
    ):
        """测试文件下载和缩略图功能的完整流程 - 需求 3.2"""
        # 创建临时文件用于测试
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            temp_file.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)
            temp_path = Path(temp_file.name)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as thumb_file:
            thumb_file.write(b'\xFF\xD8\xFF' + b'\x00' * 500)
            thumb_path = Path(thumb_file.name)
        
        try:
            # 创建测试附件记录
            attachment = PromptAttachment(
                prompt_id=image_prompt.id,
                filename="download_test.png",
                original_filename="original_download_test.png",
                file_size=1024,
                mime_type="image/png",
                file_path="attachments/download_test.png",
                thumbnail_path="thumbnails/download_test_thumb.jpg",
                file_metadata={"width": 400, "height": 300}
            )
            db_session.add(attachment)
            db_session.commit()
            db_session.refresh(attachment)
            
            # 步骤 1: 测试文件下载
            with patch.object(file_storage_service, 'get_file_path') as mock_get_path, \
                 patch.object(file_storage_service, 'file_exists') as mock_exists:
                
                mock_get_path.return_value = temp_path
                mock_exists.return_value = True
                
                download_response = client.get(f"/api/v1/attachments/{attachment.id}/download")
                
                assert download_response.status_code == status.HTTP_200_OK
                assert download_response.headers["content-type"] == "image/png"
                assert "attachment; filename=" in download_response.headers.get("content-disposition", "")
            
            # 步骤 2: 测试缩略图获取
            with patch.object(file_storage_service, 'get_file_path') as mock_get_thumb_path, \
                 patch.object(file_storage_service, 'file_exists') as mock_thumb_exists:
                
                mock_get_thumb_path.return_value = thumb_path
                mock_thumb_exists.return_value = True
                
                thumbnail_response = client.get(f"/api/v1/attachments/{attachment.id}/thumbnail")
                
                assert thumbnail_response.status_code == status.HTTP_200_OK
                assert thumbnail_response.headers["content-type"] == "image/jpeg"
            
            # 步骤 3: 测试文件不存在的情况
            with patch.object(file_storage_service, 'file_exists') as mock_not_exists:
                mock_not_exists.return_value = False
                
                not_found_response = client.get(f"/api/v1/attachments/{attachment.id}/download")
                assert not_found_response.status_code == status.HTTP_404_NOT_FOUND
                assert "文件不存在" in not_found_response.json()["detail"]
            
            # 步骤 4: 测试没有缩略图的附件
            no_thumb_attachment = PromptAttachment(
                prompt_id=image_prompt.id,
                filename="no_thumb_test.txt",
                original_filename="no_thumb_test.txt",
                file_size=512,
                mime_type="text/plain",
                file_path="attachments/no_thumb_test.txt",
                thumbnail_path=None
            )
            db_session.add(no_thumb_attachment)
            db_session.commit()
            
            no_thumb_response = client.get(f"/api/v1/attachments/{no_thumb_attachment.id}/thumbnail")
            assert no_thumb_response.status_code == status.HTTP_404_NOT_FOUND
            assert "没有缩略图" in no_thumb_response.json()["detail"]
            
        finally:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            if thumb_path.exists():
                thumb_path.unlink()

    def test_media_type_validation_workflow(
        self, 
        client: TestClient, 
        db_session: Session,
        image_prompt: Prompt
    ):
        """测试媒体类型验证的完整流程 - 需求 2.4"""
        # 步骤 1: 测试正确的文件类型上传
        valid_files = [
            ("test.jpg", "image/jpeg", b'\xFF\xD8\xFF' + b'\x00' * 500),
            ("test.png", "image/png", b'\x89PNG\r\n\x1a\n' + b'\x00' * 500),
            ("test.gif", "image/gif", b'GIF89a' + b'\x00' * 500),
            ("test.webp", "image/webp", b'RIFF' + b'\x00' * 4 + b'WEBP' + b'\x00' * 500)
        ]
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
             patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
             patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
             patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
            
            def mock_save_file_side_effect(file, subdir):
                filename = f"valid_{file.filename}"
                return filename, f"{subdir}/{filename}"
            
            mock_save_file.side_effect = mock_save_file_side_effect
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_valid.jpg", 
                {"width": 100, "height": 100}
            )
            mock_save_binary.return_value = "thumbnails/thumb_valid.jpg"
            
            for filename, mime_type, content in valid_files:
                response = client.post(
                    f"/api/v1/prompts/{image_prompt.id}/attachments",
                    files={"file": (filename, content, mime_type)}
                )
                assert response.status_code == status.HTTP_201_CREATED, f"Failed for {filename}"
        
        # 步骤 2: 测试无效的文件类型
        invalid_files = [
            ("test.exe", "application/octet-stream", b'MZ\x90\x00' + b'\x00' * 100),
            ("test.pdf", "application/pdf", b'%PDF-1.4' + b'\x00' * 100),  # PDF 对图片类型无效
            ("test.txt", "text/plain", b'This is a text file'),
            ("test.zip", "application/zip", b'PK\x03\x04' + b'\x00' * 100)
        ]
        
        for filename, mime_type, content in invalid_files:
            response = client.post(
                f"/api/v1/prompts/{image_prompt.id}/attachments",
                files={"file": (filename, content, mime_type)}
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST, f"Should fail for {filename}"
        
        # 步骤 3: 测试文件大小限制
        large_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * (15 * 1024 * 1024)  # 15MB
        
        large_file_response = client.post(
            f"/api/v1/prompts/{image_prompt.id}/attachments",
            files={"file": ("large_image.png", large_content, "image/png")}
        )
        assert large_file_response.status_code == status.HTTP_400_BAD_REQUEST
        assert "文件大小" in large_file_response.json()["detail"]

    def test_storage_statistics_workflow(
        self, 
        client: TestClient, 
        db_session: Session,
        image_prompt: Prompt,
        sample_prompt_class
    ):
        """测试存储统计功能的完整流程"""
        # 创建不同类型的提示词
        doc_prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="文档提示词",
            description="文档类型提示词",
            media_type=MediaType.DOCUMENT
        )
        audio_prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="音频提示词",
            description="音频类型提示词",
            media_type=MediaType.AUDIO
        )
        db_session.add_all([doc_prompt, audio_prompt])
        db_session.commit()
        
        # 创建不同类型的附件
        attachments = [
            PromptAttachment(
                prompt_id=image_prompt.id,
                filename="stats_image.jpg",
                original_filename="stats_image.jpg",
                file_size=2048,
                mime_type="image/jpeg",
                file_path="attachments/stats_image.jpg"
            ),
            PromptAttachment(
                prompt_id=doc_prompt.id,
                filename="stats_doc.pdf",
                original_filename="stats_doc.pdf",
                file_size=4096,
                mime_type="application/pdf",
                file_path="attachments/stats_doc.pdf"
            ),
            PromptAttachment(
                prompt_id=audio_prompt.id,
                filename="stats_audio.mp3",
                original_filename="stats_audio.mp3",
                file_size=8192,
                mime_type="audio/mpeg",
                file_path="attachments/stats_audio.mp3"
            )
        ]
        
        for attachment in attachments:
            db_session.add(attachment)
        db_session.commit()
        
        # 步骤 1: 获取存储统计
        with patch('app.services.file_storage.file_storage_service.get_storage_info') as mock_storage_info:
            mock_storage_info.return_value = {
                "storage_type": "local",
                "total_size": 14336,  # 2048 + 4096 + 8192
                "file_count": 3
            }
            
            stats_response = client.get("/api/v1/statistics")
            assert stats_response.status_code == status.HTTP_200_OK
            
            stats_data = stats_response.json()
            assert stats_data["total_attachments"] == 3
            assert "attachments_by_type" in stats_data
            assert stats_data["storage_info"]["total_size"] == 14336
        
        # 步骤 2: 获取媒体类型统计
        media_stats_response = client.get("/api/v1/media-types/statistics")
        assert media_stats_response.status_code == status.HTTP_200_OK
        
        media_stats_data = media_stats_response.json()
        assert media_stats_data["total_prompts"] >= 3
        assert "by_media_type" in media_stats_data

    def test_error_handling_workflow(
        self, 
        client: TestClient, 
        db_session: Session,
        image_prompt: Prompt
    ):
        """测试错误处理的完整流程"""
        # 步骤 1: 测试上传到不存在的提示词
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 500
        
        not_found_response = client.post(
            "/api/v1/prompts/99999/attachments",
            files={"file": ("test.png", png_content, "image/png")}
        )
        assert not_found_response.status_code == status.HTTP_404_NOT_FOUND
        assert "提示词不存在" in not_found_response.json()["detail"]
        
        # 步骤 2: 测试访问不存在的附件
        get_not_found_response = client.get("/api/v1/attachments/99999")
        assert get_not_found_response.status_code == status.HTTP_404_NOT_FOUND
        
        # 步骤 3: 测试删除不存在的附件
        delete_not_found_response = client.delete("/api/v1/attachments/99999")
        assert delete_not_found_response.status_code == status.HTTP_404_NOT_FOUND
        
        # 步骤 4: 测试无效的媒体类型
        invalid_media_type_response = client.get("/api/v1/media-types/invalid/info")
        assert invalid_media_type_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 步骤 5: 测试存储失败的情况
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file:
            mock_save_file.side_effect = OSError("存储空间不足")
            
            storage_error_response = client.post(
                f"/api/v1/prompts/{image_prompt.id}/attachments",
                files={"file": ("test.png", png_content, "image/png")}
            )
            assert storage_error_response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "附件上传失败" in storage_error_response.json()["detail"]