"""附件 API 端点测试

测试附件管理相关的 API 端点，包括：
- 文件上传接口
- 附件列表查询
- 附件下载和缩略图
- 附件删除
- 错误处理
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.attachment import PromptAttachment
from app.models.prompt import Prompt, MediaType
from app.services.file_storage import file_storage_service


class TestAttachmentAPI:
    """附件 API 测试类"""

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
    def sample_attachment(self, db_session: Session, sample_prompt: Prompt) -> PromptAttachment:
        """创建测试用的附件"""
        attachment = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.png",
            original_filename="original_test.png",
            file_size=1024,
            mime_type="image/png",
            file_path="attachments/test_file.png",
            thumbnail_path="thumbnails/test_thumb.jpg",
            file_metadata={"width": 100, "height": 100}
        )
        db_session.add(attachment)
        db_session.commit()
        db_session.refresh(attachment)
        return attachment

    def test_upload_attachment_success(self, client: TestClient, sample_prompt: Prompt):
        """测试成功上传附件"""
        # 创建测试文件
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
             patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
             patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
             patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
            
            # 设置 mock 返回值
            mock_save_file.return_value = ("unique_filename.png", "attachments/unique_filename.png")
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_unique_filename.jpg", 
                {"width": 100, "height": 100}
            )
            mock_save_binary.return_value = "thumbnails/thumb_unique_filename.jpg"
            
            # 发送上传请求
            response = client.post(
                f"/api/v1/prompts/{sample_prompt.id}/attachments",
                files={"file": ("test.png", png_content, "image/png")}
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            data = response.json()
            assert data["message"] == "文件上传成功"
            assert data["attachment"]["original_filename"] == "test.png"
            assert data["attachment"]["mime_type"] == "image/png"
            assert data["attachment"]["prompt_id"] == sample_prompt.id

    def test_upload_attachment_no_file(self, client: TestClient, sample_prompt: Prompt):
        """测试上传时没有提供文件"""
        response = client.post(f"/api/v1/prompts/{sample_prompt.id}/attachments")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_attachment_prompt_not_found(self, client: TestClient):
        """测试上传到不存在的提示词"""
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        
        response = client.post(
            "/api/v1/prompts/99999/attachments",
            files={"file": ("test.png", png_content, "image/png")}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "提示词不存在" in response.json()["detail"]

    def test_upload_attachment_invalid_file_type(self, client: TestClient, sample_prompt: Prompt):
        """测试上传无效文件类型"""
        # 创建可执行文件内容
        exe_content = b'MZ\x90\x00' + b'\x00' * 100
        
        response = client.post(
            f"/api/v1/prompts/{sample_prompt.id}/attachments",
            files={"file": ("test.exe", exe_content, "application/octet-stream")}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_attachment_with_media_type(self, client: TestClient, sample_prompt: Prompt):
        """测试指定媒体类型上传附件"""
        txt_content = b"This is a test document."
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file:
            mock_save_file.return_value = ("unique_filename.txt", "attachments/unique_filename.txt")
            
            response = client.post(
                f"/api/v1/prompts/{sample_prompt.id}/attachments?media_type=document",
                files={"file": ("test.txt", txt_content, "text/plain")}
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            data = response.json()
            assert data["attachment"]["mime_type"] == "text/plain"

    def test_list_prompt_attachments_success(
        self, 
        client: TestClient, 
        sample_prompt: Prompt,
        sample_attachment: PromptAttachment
    ):
        """测试成功获取附件列表"""
        with patch('app.services.attachment.attachment_service.get_attachment_download_url') as mock_download_url, \
             patch('app.services.attachment.attachment_service.get_attachment_thumbnail_url') as mock_thumb_url:
            
            mock_download_url.return_value = "http://localhost/download/1"
            mock_thumb_url.return_value = "http://localhost/thumbnail/1"
            
            response = client.get(f"/api/v1/prompts/{sample_prompt.id}/attachments")
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["id"] == sample_attachment.id
            assert data["items"][0]["download_url"] == "http://localhost/download/1"

    def test_list_prompt_attachments_with_pagination(
        self, 
        client: TestClient, 
        db_session: Session,
        sample_prompt: Prompt
    ):
        """测试分页获取附件列表"""
        # 创建多个附件
        for i in range(5):
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
        
        with patch('app.services.attachment.attachment_service.get_attachment_download_url') as mock_download_url, \
             patch('app.services.attachment.attachment_service.get_attachment_thumbnail_url') as mock_thumb_url:
            
            mock_download_url.return_value = "http://localhost/download/1"
            mock_thumb_url.return_value = None
            
            # 测试分页参数
            response = client.get(
                f"/api/v1/prompts/{sample_prompt.id}/attachments?skip=1&limit=2"
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["total"] == 5
            assert len(data["items"]) == 2

    def test_get_attachment_success(
        self, 
        client: TestClient, 
        sample_attachment: PromptAttachment
    ):
        """测试成功获取单个附件信息"""
        with patch('app.services.attachment.attachment_service.get_attachment_download_url') as mock_download_url, \
             patch('app.services.attachment.attachment_service.get_attachment_thumbnail_url') as mock_thumb_url:
            
            mock_download_url.return_value = "http://localhost/download/1"
            mock_thumb_url.return_value = "http://localhost/thumbnail/1"
            
            response = client.get(f"/api/v1/attachments/{sample_attachment.id}")
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["id"] == sample_attachment.id
            assert data["filename"] == sample_attachment.filename
            assert data["download_url"] == "http://localhost/download/1"

    def test_get_attachment_not_found(self, client: TestClient):
        """测试获取不存在的附件"""
        response = client.get("/api/v1/attachments/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "附件不存在" in response.json()["detail"]

    def test_download_attachment_success(
        self, 
        client: TestClient, 
        sample_attachment: PromptAttachment
    ):
        """测试成功下载附件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test file content")
            temp_path = Path(temp_file.name)
        
        try:
            with patch.object(file_storage_service, 'get_file_path') as mock_get_path, \
                 patch.object(file_storage_service, 'file_exists') as mock_exists:
                
                mock_get_path.return_value = temp_path
                mock_exists.return_value = True
                
                response = client.get(f"/api/v1/attachments/{sample_attachment.id}/download")
                
                assert response.status_code == status.HTTP_200_OK
                assert response.headers["content-type"] == sample_attachment.mime_type
        finally:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()

    def test_download_attachment_not_found(
        self, 
        client: TestClient, 
        sample_attachment: PromptAttachment
    ):
        """测试下载不存在的附件文件"""
        with patch.object(file_storage_service, 'file_exists') as mock_exists:
            mock_exists.return_value = False
            
            response = client.get(f"/api/v1/attachments/{sample_attachment.id}/download")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "文件不存在" in response.json()["detail"]

    def test_get_attachment_thumbnail_success(
        self, 
        client: TestClient, 
        sample_attachment: PromptAttachment
    ):
        """测试成功获取附件缩略图"""
        # 创建临时缩略图文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"thumbnail content")
            temp_path = Path(temp_file.name)
        
        try:
            with patch.object(file_storage_service, 'get_file_path') as mock_get_path, \
                 patch.object(file_storage_service, 'file_exists') as mock_exists:
                
                mock_get_path.return_value = temp_path
                mock_exists.return_value = True
                
                response = client.get(f"/api/v1/attachments/{sample_attachment.id}/thumbnail")
                
                assert response.status_code == status.HTTP_200_OK
                assert response.headers["content-type"] == "image/jpeg"
        finally:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()

    def test_get_attachment_thumbnail_no_thumbnail(
        self, 
        client: TestClient, 
        db_session: Session,
        sample_prompt: Prompt
    ):
        """测试获取没有缩略图的附件"""
        # 创建没有缩略图的附件
        attachment = PromptAttachment(
            prompt_id=sample_prompt.id,
            filename="test_file.txt",
            original_filename="original_test.txt",
            file_size=1024,
            mime_type="text/plain",
            file_path="attachments/test_file.txt",
            thumbnail_path=None
        )
        db_session.add(attachment)
        db_session.commit()
        
        response = client.get(f"/api/v1/attachments/{attachment.id}/thumbnail")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "没有缩略图" in response.json()["detail"]

    def test_update_attachment_success(
        self, 
        client: TestClient, 
        sample_attachment: PromptAttachment
    ):
        """测试成功更新附件信息"""
        update_data = {
            "filename": "updated_filename.png",
            "file_metadata": {"description": "更新的描述"}
        }
        
        with patch('app.services.attachment.attachment_service.get_attachment_download_url') as mock_download_url, \
             patch('app.services.attachment.attachment_service.get_attachment_thumbnail_url') as mock_thumb_url:
            
            mock_download_url.return_value = "http://localhost/download/1"
            mock_thumb_url.return_value = "http://localhost/thumbnail/1"
            
            response = client.put(
                f"/api/v1/attachments/{sample_attachment.id}",
                json=update_data
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["filename"] == "updated_filename.png"

    def test_update_attachment_not_found(self, client: TestClient):
        """测试更新不存在的附件"""
        update_data = {"filename": "new_name.png"}
        
        response = client.put("/api/v1/attachments/99999", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_attachment_success(
        self, 
        client: TestClient, 
        sample_attachment: PromptAttachment
    ):
        """测试成功删除附件"""
        with patch('app.services.file_storage.file_storage_service.delete_file') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f"/api/v1/attachments/{sample_attachment.id}")
            
            assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_attachment_not_found(self, client: TestClient):
        """测试删除不存在的附件"""
        response = client.delete("/api/v1/attachments/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_prompt_attachments_success(
        self, 
        client: TestClient, 
        db_session: Session,
        sample_prompt: Prompt
    ):
        """测试成功删除提示词的所有附件"""
        # 创建多个附件
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
        
        with patch('app.services.file_storage.file_storage_service.delete_file') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f"/api/v1/prompts/{sample_prompt.id}/attachments")
            
            assert response.status_code == status.HTTP_204_NO_CONTENT
            assert response.headers["X-Deleted-Count"] == "3"

    def test_get_storage_statistics(self, client: TestClient, sample_attachment: PromptAttachment):
        """测试获取存储统计信息"""
        with patch('app.services.file_storage.file_storage_service.get_storage_info') as mock_storage_info:
            mock_storage_info.return_value = {
                "storage_type": "local",
                "total_size": 1024,
                "file_count": 1
            }
            
            response = client.get("/api/v1/attachments/statistics")
            
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert "total_attachments" in data
            assert "attachments_by_type" in data
            assert "storage_info" in data


class TestMediaTypeAPI:
    """媒体类型 API 测试类"""

    def test_get_media_types(self, client: TestClient):
        """测试获取支持的媒体类型"""
        response = client.get("/api/v1/media-types/")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5  # TEXT, IMAGE, DOCUMENT, AUDIO, VIDEO
        
        # 验证每个媒体类型的结构
        for media_type in data:
            assert "value" in media_type
            assert "label" in media_type
            assert "description" in media_type
            assert "icon" in media_type
            assert "supported_formats" in media_type

    def test_get_media_type_statistics(self, client: TestClient, db_session: Session):
        """测试获取媒体类型统计"""
        # 创建提示词分类
        from app.models.prompt import PromptClass
        prompt_class = PromptClass(
            name="统计测试分类",
            description="用于统计测试的分类"
        )
        db_session.add(prompt_class)
        db_session.commit()
        
        # 创建不同类型的提示词
        prompts = [
            Prompt(class_id=prompt_class.id, name="文本提示词", media_type=MediaType.TEXT),
            Prompt(class_id=prompt_class.id, name="图片提示词1", media_type=MediaType.IMAGE),
            Prompt(class_id=prompt_class.id, name="图片提示词2", media_type=MediaType.IMAGE),
            Prompt(class_id=prompt_class.id, name="文档提示词", media_type=MediaType.DOCUMENT),
        ]
        
        for prompt in prompts:
            db_session.add(prompt)
        
        db_session.commit()
        
        response = client.get("/api/v1/media-types/statistics")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["total_prompts"] == 4
        assert data["by_media_type"]["text"]["count"] == 1
        assert data["by_media_type"]["image"]["count"] == 2
        assert data["by_media_type"]["document"]["count"] == 1
        assert data["most_used"] == "image"

    def test_get_media_type_info(self, client: TestClient):
        """测试获取特定媒体类型信息"""
        response = client.get("/api/v1/media-types/image/info")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["value"] == "image"
        assert data["label"] == "图片"
        assert "supported_formats" in data
        assert "validation_rules" in data
        assert "features" in data

    def test_get_media_type_validation_rules(self, client: TestClient):
        """测试获取媒体类型验证规则"""
        response = client.get("/api/v1/media-types/image/validation-rules")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["media_type"] == "image"
        assert "validation_rules" in data
        assert "supported_formats" in data
        assert "max_size" in data
        assert "max_size_mb" in data

    def test_get_invalid_media_type_info(self, client: TestClient):
        """测试获取无效媒体类型信息"""
        response = client.get("/api/v1/media-types/invalid/info")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY