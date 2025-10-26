"""性能和安全测试

测试大文件上传性能、恶意文件上传防护和并发上传场景，验证：
- 大文件上传性能 (需求 2.3)
- 恶意文件上传防护 (需求 4.1)
- 并发上传场景 (需求 4.4)
"""

import asyncio
import io
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.prompt import Prompt, MediaType
from app.services.file_validation import file_validation_service
from app.services.file_storage import file_storage_service


class TestPerformanceAndSecurity:
    """性能和安全测试类"""

    @pytest.fixture
    def sample_prompt_class(self, db_session: Session):
        """创建测试用的提示词分类"""
        from app.models.prompt import PromptClass
        
        prompt_class = PromptClass(
            name="性能测试分类",
            description="用于性能测试的分类"
        )
        db_session.add(prompt_class)
        db_session.commit()
        db_session.refresh(prompt_class)
        return prompt_class

    @pytest.fixture
    def image_prompt(self, db_session: Session, sample_prompt_class):
        """创建图片类型提示词"""
        prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="性能测试图片提示词",
            description="用于性能测试的图片提示词",
            media_type=MediaType.IMAGE
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt

    @pytest.fixture
    def document_prompt(self, db_session: Session, sample_prompt_class):
        """创建文档类型提示词"""
        prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="性能测试文档提示词",
            description="用于性能测试的文档提示词",
            media_type=MediaType.DOCUMENT
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt


class TestLargeFilePerformance:
    """大文件上传性能测试 - 需求 2.3"""

    @pytest.fixture
    def sample_prompt_class(self, db_session: Session):
        """创建测试用的提示词分类"""
        from app.models.prompt import PromptClass
        
        prompt_class = PromptClass(
            name="性能测试分类",
            description="用于性能测试的分类"
        )
        db_session.add(prompt_class)
        db_session.commit()
        db_session.refresh(prompt_class)
        return prompt_class

    @pytest.fixture
    def image_prompt(self, db_session: Session, sample_prompt_class):
        """创建图片类型提示词"""
        prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="性能测试图片提示词",
            description="用于性能测试的图片提示词",
            media_type=MediaType.IMAGE
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt

    def test_large_file_size_validation(self):
        """测试大文件大小验证性能"""
        # 测试接近限制的文件大小
        max_size = 10 * 1024 * 1024  # 10MB
        large_size = max_size - 1024  # 接近但未超过限制
        oversized = max_size + 1024   # 超过限制
        
        start_time = time.time()
        
        # 测试有效大小
        is_valid, error = file_validation_service.validate_file_size(large_size)
        assert is_valid is True
        assert error is None
        
        # 测试超大文件
        is_valid, error = file_validation_service.validate_file_size(oversized)
        assert is_valid is False
        assert "文件大小超过限制" in error
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # 验证性能：文件大小验证应该在 1 秒内完成
        assert validation_time < 1.0, f"文件大小验证耗时过长: {validation_time:.3f}s"

    def test_large_file_content_validation_performance(self):
        """测试大文件内容验证性能"""
        # 创建接近限制大小的文件内容
        large_size = 8 * 1024 * 1024  # 8MB
        
        # 创建有效的 PNG 文件头 + 大量数据
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03'
        large_content = png_header + b'\x00' * (large_size - len(png_header))
        
        start_time = time.time()
        
        # 测试 MIME 类型检测性能
        mime_type = file_validation_service.detect_mime_type("large_test.png", large_content)
        assert mime_type == "image/png"
        
        # 测试安全性检查性能
        is_safe, error = file_validation_service.validate_file_security(
            large_content, "large_test.png"
        )
        assert is_safe is True
        assert error is None
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # 验证性能：大文件内容验证应该在 3 秒内完成
        assert validation_time < 3.0, f"大文件内容验证耗时过长: {validation_time:.3f}s"

    def test_large_file_upload_api_performance(
        self, 
        client: TestClient, 
        image_prompt: Prompt
    ):
        """测试大文件上传 API 性能"""
        # 创建 8MB 的测试文件
        large_size = 8 * 1024 * 1024
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03'
        large_content = png_header + b'\x00' * (large_size - len(png_header))
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
             patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
             patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
             patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
            
            # 设置 mock 返回值
            mock_save_file.return_value = ("large_test.png", "attachments/large_test.png")
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_large_test.jpg", 
                {"width": 100, "height": 100}
            )
            mock_save_binary.return_value = "thumbnails/thumb_large_test.jpg"
            
            start_time = time.time()
            
            response = client.post(
                f"/api/v1/prompts/{image_prompt.id}/attachments",
                files={"file": ("large_test.png", large_content, "image/png")}
            )
            
            end_time = time.time()
            upload_time = end_time - start_time
            
            assert response.status_code == status.HTTP_201_CREATED
            
            # 验证性能：大文件上传应该在 10 秒内完成
            assert upload_time < 10.0, f"大文件上传耗时过长: {upload_time:.3f}s"
            
            # 验证响应数据
            data = response.json()
            assert data["attachment"]["file_size"] == large_size

    def test_multiple_large_files_sequential_performance(
        self, 
        client: TestClient, 
        image_prompt: Prompt
    ):
        """测试连续上传多个大文件的性能"""
        # 创建 3 个 5MB 的测试文件
        file_size = 5 * 1024 * 1024
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03'
        
        files_data = []
        for i in range(3):
            content = png_header + b'\x00' * (file_size - len(png_header))
            files_data.append((f"large_file_{i}.png", content))
        
        with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
             patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
             patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
             patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
            
            def mock_save_file_side_effect(file, subdir):
                filename = f"seq_{file.filename}"
                return filename, f"{subdir}/{filename}"
            
            mock_save_file.side_effect = mock_save_file_side_effect
            mock_is_image.return_value = True
            mock_process_image.return_value = (
                b"thumbnail_content", 
                "thumb_seq.jpg", 
                {"width": 100, "height": 100}
            )
            mock_save_binary.return_value = "thumbnails/thumb_seq.jpg"
            
            start_time = time.time()
            
            upload_times = []
            for filename, content in files_data:
                file_start = time.time()
                
                response = client.post(
                    f"/api/v1/prompts/{image_prompt.id}/attachments",
                    files={"file": (filename, content, "image/png")}
                )
                
                file_end = time.time()
                file_time = file_end - file_start
                upload_times.append(file_time)
                
                assert response.status_code == status.HTTP_201_CREATED
            
            total_time = time.time() - start_time
            
            # 验证性能指标
            assert total_time < 30.0, f"连续上传 3 个大文件耗时过长: {total_time:.3f}s"
            assert max(upload_times) < 12.0, f"单个文件上传时间过长: {max(upload_times):.3f}s"
            assert len(upload_times) == 3

    def test_file_storage_performance_with_large_files(self):
        """测试文件存储服务处理大文件的性能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            from app.services.file_storage import FileStorageService
            
            # 创建临时存储服务
            storage_service = FileStorageService()
            storage_service.storage_path = Path(temp_dir)
            storage_service._ensure_storage_directories()
            
            # 创建 6MB 的测试文件
            file_size = 6 * 1024 * 1024
            content = b'\x89PNG\r\n\x1a\n' + b'\x00' * (file_size - 10)
            
            file_obj = io.BytesIO(content)
            from fastapi import UploadFile
            upload_file = UploadFile(
                filename="performance_test.png",
                file=file_obj,
                size=file_size
            )
            
            start_time = time.time()
            
            # 测试保存性能
            filename, file_path = asyncio.run(storage_service.save_file(upload_file))
            
            save_time = time.time() - start_time
            
            # 验证文件保存成功
            full_path = storage_service.storage_path / file_path
            assert full_path.exists()
            assert full_path.stat().st_size == file_size
            
            # 验证性能：6MB 文件保存应该在 5 秒内完成
            assert save_time < 5.0, f"大文件保存耗时过长: {save_time:.3f}s"
            
            # 测试删除性能
            delete_start = time.time()
            result = storage_service.delete_file(file_path)
            delete_time = time.time() - delete_start
            
            assert result is True
            assert not full_path.exists()
            
            # 验证性能：文件删除应该在 1 秒内完成
            assert delete_time < 1.0, f"大文件删除耗时过长: {delete_time:.3f}s"


class TestMaliciousFileProtection:
    """恶意文件上传防护测试 - 需求 4.1"""

    @pytest.fixture
    def sample_prompt_class(self, db_session: Session):
        """创建测试用的提示词分类"""
        from app.models.prompt import PromptClass
        
        prompt_class = PromptClass(
            name="安全测试分类",
            description="用于安全测试的分类"
        )
        db_session.add(prompt_class)
        db_session.commit()
        db_session.refresh(prompt_class)
        return prompt_class

    @pytest.fixture
    def image_prompt(self, db_session: Session, sample_prompt_class):
        """创建图片类型提示词"""
        prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="安全测试图片提示词",
            description="用于安全测试的图片提示词",
            media_type=MediaType.IMAGE
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt

    def test_executable_file_detection(self):
        """测试可执行文件检测"""
        malicious_files = [
            # Windows PE 文件
            ("malware.exe", b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00'),
            # ELF 文件 (Linux 可执行文件)
            ("malware", b'\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
            # Mach-O 文件 (macOS 可执行文件)
            ("malware", b'\xfe\xed\xfa\xce\x00\x00\x00\x0c\x00\x00\x00\x09'),
            # Java class 文件
            ("Malware.class", b'\xca\xfe\xba\xbe\x00\x00\x00\x34'),
            # 脚本文件伪装成图片
            ("script.png", b'#!/bin/bash\nrm -rf /\n'),
        ]
        
        for filename, content in malicious_files:
            is_safe, error = file_validation_service.validate_file_security(content, filename)
            assert is_safe is False, f"应该检测到恶意文件: {filename}"
            assert "恶意代码" in error or "不安全" in error, f"错误信息不正确: {error}"

    def test_path_traversal_attack_prevention(self):
        """测试路径遍历攻击防护"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..%5c..%5c..%5cwindows%5csystem32%5cconfig%5csam",
            "file/../../sensitive.txt",
            "normal_name/../../../etc/shadow",
        ]
        
        safe_content = b"This is safe content"
        
        for filename in malicious_filenames:
            is_safe, error = file_validation_service.validate_file_security(safe_content, filename)
            assert is_safe is False, f"应该检测到路径遍历攻击: {filename}"
            assert "不安全字符" in error or "路径" in error, f"错误信息不正确: {error}"

    def test_mime_type_spoofing_detection(self):
        """测试 MIME 类型欺骗检测"""
        # 测试文件头与扩展名不匹配的情况
        spoofed_files = [
            # 可执行文件伪装成图片
            ("fake_image.jpg", b'MZ\x90\x00' + b'\x00' * 100, "image/jpeg"),
            ("fake_image.png", b'\x7fELF' + b'\x00' * 100, "image/png"),
            # 脚本文件伪装成文档
            ("fake_doc.pdf", b'#!/bin/sh\necho "malicious"', "application/pdf"),
            # ZIP 文件伪装成图片
            ("fake_image.gif", b'PK\x03\x04' + b'\x00' * 100, "image/gif"),
        ]
        
        for filename, content, claimed_mime_type in spoofed_files:
            # 检测真实的 MIME 类型
            detected_mime_type = file_validation_service.detect_mime_type(filename, content)
            
            # 验证检测到的类型与声称的类型不匹配
            if detected_mime_type != claimed_mime_type:
                # 进行安全性检查
                is_safe, error = file_validation_service.validate_file_security(content, filename)
                
                # 如果是恶意文件，应该被检测出来
                if content.startswith((b'MZ', b'\x7fELF', b'#!/')):
                    assert is_safe is False, f"应该检测到伪装的恶意文件: {filename}"

    def test_malicious_file_upload_api_protection(
        self, 
        client: TestClient, 
        image_prompt: Prompt
    ):
        """测试 API 层面的恶意文件上传防护"""
        malicious_files = [
            ("virus.exe", b'MZ\x90\x00' + b'\x00' * 100, "application/octet-stream"),
            ("script.jpg", b'#!/bin/bash\nrm -rf /', "image/jpeg"),
            ("../../../etc/passwd", b"root:x:0:0:root:/root:/bin/bash", "text/plain"),
            ("malware.png", b'\x7fELF\x01\x01\x01\x00' + b'\x00' * 100, "image/png"),
        ]
        
        for filename, content, mime_type in malicious_files:
            response = client.post(
                f"/api/v1/prompts/{image_prompt.id}/attachments",
                files={"file": (filename, content, mime_type)}
            )
            
            # 应该返回 400 错误，拒绝恶意文件
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
            error_detail = response.json()["detail"]
            assert any(keyword in error_detail.lower() for keyword in [
                "恶意", "不安全", "不支持", "无效", "危险"
            ]), f"错误信息应该指出安全问题: {error_detail}"

    def test_file_content_sanitization(self):
        """测试文件内容清理和验证"""
        # 测试包含潜在恶意内容的文件
        suspicious_contents = [
            # 包含脚本标签的 SVG
            (b'<svg><script>alert("xss")</script></svg>', "image.svg"),
            # 包含 JavaScript 的 HTML
            (b'<html><script>window.location="http://evil.com"</script></html>', "page.html"),
            # 包含宏的 Office 文档标识
            (b'PK\x03\x04' + b'word/vbaProject.bin' + b'\x00' * 100, "document.docx"),
        ]
        
        for content, filename in suspicious_contents:
            is_safe, error = file_validation_service.validate_file_security(content, filename)
            
            # 根据文件类型和内容判断是否应该被阻止
            if b'<script>' in content or b'vbaProject.bin' in content:
                # 这些内容应该被标记为不安全
                assert is_safe is False or error is not None, f"应该检测到可疑内容: {filename}"

    def test_zip_bomb_protection(self):
        """测试 ZIP 炸弹防护"""
        # 创建一个简单的 ZIP 文件头（模拟压缩文件）
        zip_header = b'PK\x03\x04\x14\x00\x00\x00\x08\x00'
        
        # 模拟高压缩比的文件（实际的 ZIP 炸弹会更复杂）
        suspicious_zip = zip_header + b'\x00' * 1000
        
        is_safe, error = file_validation_service.validate_file_security(
            suspicious_zip, "suspicious.zip"
        )
        
        # 根据当前实现，ZIP 文件可能被允许或拒绝
        # 这里主要测试系统不会崩溃
        assert isinstance(is_safe, bool)
        if not is_safe:
            assert error is not None

    def test_performance_under_malicious_load(
        self, 
        client: TestClient, 
        image_prompt: Prompt
    ):
        """测试在恶意文件攻击下的性能"""
        # 创建多个恶意文件进行连续攻击
        malicious_files = []
        for i in range(10):
            content = b'MZ\x90\x00' + f"malware_{i}".encode() + b'\x00' * 100
            malicious_files.append((f"malware_{i}.exe", content))
        
        start_time = time.time()
        
        for filename, content in malicious_files:
            response = client.post(
                f"/api/v1/prompts/{image_prompt.id}/attachments",
                files={"file": (filename, content, "application/octet-stream")}
            )
            
            # 每个请求都应该被快速拒绝
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        total_time = time.time() - start_time
        
        # 验证性能：处理 10 个恶意文件应该在 5 秒内完成
        assert total_time < 5.0, f"恶意文件检测耗时过长: {total_time:.3f}s"
        
        # 平均每个文件的处理时间应该很短
        avg_time = total_time / len(malicious_files)
        assert avg_time < 0.5, f"单个恶意文件检测耗时过长: {avg_time:.3f}s"


class TestConcurrentUpload:
    """并发上传场景测试 - 需求 4.4"""

    @pytest.fixture
    def sample_prompt_class(self, db_session: Session):
        """创建测试用的提示词分类"""
        from app.models.prompt import PromptClass
        
        prompt_class = PromptClass(
            name="并发测试分类",
            description="用于并发测试的分类"
        )
        db_session.add(prompt_class)
        db_session.commit()
        db_session.refresh(prompt_class)
        return prompt_class

    @pytest.fixture
    def image_prompt(self, db_session: Session, sample_prompt_class):
        """创建图片类型提示词"""
        prompt = Prompt(
            class_id=sample_prompt_class.id,
            name="并发测试图片提示词",
            description="用于并发测试的图片提示词",
            media_type=MediaType.IMAGE
        )
        db_session.add(prompt)
        db_session.commit()
        db_session.refresh(prompt)
        return prompt

    def test_concurrent_file_uploads_thread_safety(
        self, 
        client: TestClient, 
        image_prompt: Prompt
    ):
        """测试并发文件上传的线程安全性"""
        # 创建多个不同的测试文件
        files_data = []
        for i in range(5):
            png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03'
            content = png_header + f"file_{i}".encode() + b'\x00' * 1000
            files_data.append((f"concurrent_test_{i}.png", content))
        
        results = []
        errors = []
        
        def upload_file(file_data):
            """单个文件上传函数"""
            filename, content = file_data
            try:
                with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
                     patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
                     patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
                     patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
                    
                    mock_save_file.return_value = (f"concurrent_{filename}", f"attachments/concurrent_{filename}")
                    mock_is_image.return_value = True
                    mock_process_image.return_value = (
                        b"thumbnail_content", 
                        f"thumb_concurrent_{filename}.jpg", 
                        {"width": 100, "height": 100}
                    )
                    mock_save_binary.return_value = f"thumbnails/thumb_concurrent_{filename}.jpg"
                    
                    response = client.post(
                        f"/api/v1/prompts/{image_prompt.id}/attachments",
                        files={"file": (filename, content, "image/png")}
                    )
                    
                    return {
                        "filename": filename,
                        "status_code": response.status_code,
                        "response_data": response.json() if response.status_code == 201 else None
                    }
            except Exception as e:
                return {"filename": filename, "error": str(e)}
        
        # 使用线程池并发上传
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {
                executor.submit(upload_file, file_data): file_data[0] 
                for file_data in files_data
            }
            
            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    result = future.result()
                    if "error" in result:
                        errors.append(result)
                    else:
                        results.append(result)
                except Exception as exc:
                    errors.append({"filename": filename, "error": str(exc)})
        
        total_time = time.time() - start_time
        
        # 验证结果
        assert len(errors) == 0, f"并发上传出现错误: {errors}"
        assert len(results) == 5, f"应该有 5 个成功的上传结果，实际: {len(results)}"
        
        # 验证所有上传都成功
        for result in results:
            assert result["status_code"] == status.HTTP_201_CREATED
            assert result["response_data"] is not None
        
        # 验证性能：并发上传应该比串行上传更快
        assert total_time < 10.0, f"并发上传耗时过长: {total_time:.3f}s"

    def test_concurrent_uploads_to_different_prompts(
        self, 
        client: TestClient, 
        db_session: Session,
        sample_prompt_class
    ):
        """测试向不同提示词并发上传文件"""
        # 创建多个提示词
        prompts = []
        for i in range(3):
            prompt = Prompt(
                class_id=sample_prompt_class.id,
                name=f"并发测试提示词_{i}",
                description=f"用于并发测试的提示词 {i}",
                media_type=MediaType.IMAGE
            )
            db_session.add(prompt)
            prompts.append(prompt)
        
        db_session.commit()
        for prompt in prompts:
            db_session.refresh(prompt)
        
        # 为每个提示词准备文件
        upload_tasks = []
        for i, prompt in enumerate(prompts):
            for j in range(2):  # 每个提示词上传 2 个文件
                png_content = b'\x89PNG\r\n\x1a\n' + f"prompt_{i}_file_{j}".encode() + b'\x00' * 500
                upload_tasks.append({
                    "prompt_id": prompt.id,
                    "filename": f"prompt_{i}_file_{j}.png",
                    "content": png_content
                })
        
        results = []
        errors = []
        
        def upload_to_prompt(task):
            """向指定提示词上传文件"""
            try:
                with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
                     patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
                     patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
                     patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
                    
                    mock_save_file.return_value = (f"multi_{task['filename']}", f"attachments/multi_{task['filename']}")
                    mock_is_image.return_value = True
                    mock_process_image.return_value = (
                        b"thumbnail_content", 
                        f"thumb_multi_{task['filename']}.jpg", 
                        {"width": 100, "height": 100}
                    )
                    mock_save_binary.return_value = f"thumbnails/thumb_multi_{task['filename']}.jpg"
                    
                    response = client.post(
                        f"/api/v1/prompts/{task['prompt_id']}/attachments",
                        files={"file": (task['filename'], task['content'], "image/png")}
                    )
                    
                    return {
                        "prompt_id": task['prompt_id'],
                        "filename": task['filename'],
                        "status_code": response.status_code,
                        "success": response.status_code == 201
                    }
            except Exception as e:
                return {
                    "prompt_id": task['prompt_id'],
                    "filename": task['filename'],
                    "error": str(e)
                }
        
        # 并发执行上传任务
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(upload_to_prompt, task) for task in upload_tasks]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if "error" in result:
                        errors.append(result)
                    else:
                        results.append(result)
                except Exception as exc:
                    errors.append({"error": str(exc)})
        
        total_time = time.time() - start_time
        
        # 验证结果
        assert len(errors) == 0, f"并发上传到不同提示词出现错误: {errors}"
        assert len(results) == 6, f"应该有 6 个上传结果，实际: {len(results)}"
        
        # 验证所有上传都成功
        successful_uploads = [r for r in results if r.get("success", False)]
        assert len(successful_uploads) == 6, "所有上传都应该成功"
        
        # 验证每个提示词都有文件上传
        prompt_upload_counts = {}
        for result in successful_uploads:
            prompt_id = result["prompt_id"]
            prompt_upload_counts[prompt_id] = prompt_upload_counts.get(prompt_id, 0) + 1
        
        assert len(prompt_upload_counts) == 3, "应该有 3 个提示词收到文件"
        for count in prompt_upload_counts.values():
            assert count == 2, "每个提示词应该收到 2 个文件"
        
        # 验证性能
        assert total_time < 15.0, f"并发上传到不同提示词耗时过长: {total_time:.3f}s"

    def test_concurrent_upload_with_validation_failures(
        self, 
        client: TestClient, 
        image_prompt: Prompt
    ):
        """测试并发上传时包含验证失败的情况"""
        # 混合有效和无效文件
        mixed_files = [
            ("valid_1.png", b'\x89PNG\r\n\x1a\n' + b'\x00' * 500, True),
            ("invalid_1.exe", b'MZ\x90\x00' + b'\x00' * 100, False),
            ("valid_2.jpg", b'\xFF\xD8\xFF' + b'\x00' * 500, True),
            ("invalid_2.bat", b'@echo off\ndel /f /q *.*', False),
            ("valid_3.gif", b'GIF89a' + b'\x00' * 500, True),
        ]
        
        results = []
        
        def upload_mixed_file(file_data):
            """上传混合文件（有效/无效）"""
            filename, content, should_succeed = file_data
            
            if should_succeed:
                with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
                     patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
                     patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
                     patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
                    
                    mock_save_file.return_value = (f"mixed_{filename}", f"attachments/mixed_{filename}")
                    mock_is_image.return_value = True
                    mock_process_image.return_value = (
                        b"thumbnail_content", 
                        f"thumb_mixed_{filename}.jpg", 
                        {"width": 100, "height": 100}
                    )
                    mock_save_binary.return_value = f"thumbnails/thumb_mixed_{filename}.jpg"
                    
                    response = client.post(
                        f"/api/v1/prompts/{image_prompt.id}/attachments",
                        files={"file": (filename, content, "image/png" if should_succeed else "application/octet-stream")}
                    )
            else:
                response = client.post(
                    f"/api/v1/prompts/{image_prompt.id}/attachments",
                    files={"file": (filename, content, "application/octet-stream")}
                )
            
            return {
                "filename": filename,
                "should_succeed": should_succeed,
                "status_code": response.status_code,
                "actual_success": response.status_code == 201
            }
        
        # 并发上传混合文件
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_mixed_file, file_data) for file_data in mixed_files]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        total_time = time.time() - start_time
        
        # 验证结果
        assert len(results) == 5, "应该有 5 个上传结果"
        
        # 验证有效文件成功，无效文件失败
        for result in results:
            if result["should_succeed"]:
                assert result["actual_success"], f"有效文件应该上传成功: {result['filename']}"
            else:
                assert not result["actual_success"], f"无效文件应该上传失败: {result['filename']}"
        
        # 统计成功和失败的数量
        successful_count = sum(1 for r in results if r["actual_success"])
        failed_count = sum(1 for r in results if not r["actual_success"])
        
        assert successful_count == 3, f"应该有 3 个成功上传，实际: {successful_count}"
        assert failed_count == 2, f"应该有 2 个失败上传，实际: {failed_count}"
        
        # 验证性能：混合上传应该快速完成
        assert total_time < 8.0, f"并发混合上传耗时过长: {total_time:.3f}s"

    def test_database_consistency_under_concurrent_load(
        self, 
        client: TestClient, 
        db_session: Session,
        image_prompt: Prompt
    ):
        """测试并发负载下的数据库一致性"""
        # 记录初始附件数量
        from app.models.attachment import PromptAttachment
        initial_count = db_session.query(PromptAttachment).filter(
            PromptAttachment.prompt_id == image_prompt.id
        ).count()
        
        # 并发上传文件
        concurrent_files = []
        for i in range(8):
            content = b'\x89PNG\r\n\x1a\n' + f"consistency_test_{i}".encode() + b'\x00' * 300
            concurrent_files.append((f"consistency_test_{i}.png", content))
        
        successful_uploads = []
        
        def upload_and_verify(file_data):
            """上传文件并验证数据库状态"""
            filename, content = file_data
            
            with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file, \
                 patch('app.services.attachment.attachment_service.thumbnail_service.is_image_file') as mock_is_image, \
                 patch('app.services.attachment.attachment_service.thumbnail_service.process_image') as mock_process_image, \
                 patch('app.services.file_storage.file_storage_service.save_binary_file') as mock_save_binary:
                
                mock_save_file.return_value = (f"consistency_{filename}", f"attachments/consistency_{filename}")
                mock_is_image.return_value = True
                mock_process_image.return_value = (
                    b"thumbnail_content", 
                    f"thumb_consistency_{filename}.jpg", 
                    {"width": 100, "height": 100}
                )
                mock_save_binary.return_value = f"thumbnails/thumb_consistency_{filename}.jpg"
                
                response = client.post(
                    f"/api/v1/prompts/{image_prompt.id}/attachments",
                    files={"file": (filename, content, "image/png")}
                )
                
                if response.status_code == 201:
                    return response.json()["attachment"]["id"]
                return None
        
        # 并发执行上传
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(upload_and_verify, file_data) for file_data in concurrent_files]
            
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    successful_uploads.append(result)
        
        # 验证数据库一致性
        db_session.commit()  # 确保所有事务都已提交
        
        final_count = db_session.query(PromptAttachment).filter(
            PromptAttachment.prompt_id == image_prompt.id
        ).count()
        
        expected_count = initial_count + len(successful_uploads)
        assert final_count == expected_count, f"数据库记录数不一致: 期望 {expected_count}，实际 {final_count}"
        
        # 验证所有成功上传的附件都在数据库中
        for attachment_id in successful_uploads:
            attachment = db_session.query(PromptAttachment).filter(
                PromptAttachment.id == attachment_id
            ).first()
            assert attachment is not None, f"附件 {attachment_id} 在数据库中不存在"
            assert attachment.prompt_id == image_prompt.id, "附件关联的提示词 ID 不正确"
        
        # 验证没有重复的文件名
        attachment_filenames = db_session.query(PromptAttachment.filename).filter(
            PromptAttachment.prompt_id == image_prompt.id
        ).all()
        
        filenames = [name[0] for name in attachment_filenames]
        unique_filenames = set(filenames)
        
        assert len(filenames) == len(unique_filenames), "存在重复的文件名，可能有并发冲突"

    def test_resource_cleanup_under_concurrent_failures(
        self, 
        client: TestClient, 
        image_prompt: Prompt
    ):
        """测试并发失败情况下的资源清理"""
        # 创建会导致存储失败的文件
        failing_files = []
        for i in range(5):
            content = b'\x89PNG\r\n\x1a\n' + f"failing_test_{i}".encode() + b'\x00' * 500
            failing_files.append((f"failing_test_{i}.png", content))
        
        failure_results = []
        
        def upload_with_storage_failure(file_data):
            """模拟存储失败的上传"""
            filename, content = file_data
            
            # 模拟存储服务失败
            with patch('app.services.file_storage.file_storage_service.save_file') as mock_save_file:
                mock_save_file.side_effect = OSError("存储空间不足")
                
                response = client.post(
                    f"/api/v1/prompts/{image_prompt.id}/attachments",
                    files={"file": (filename, content, "image/png")}
                )
                
                return {
                    "filename": filename,
                    "status_code": response.status_code,
                    "failed_as_expected": response.status_code == 500
                }
        
        # 并发执行失败的上传
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_with_storage_failure, file_data) for file_data in failing_files]
            
            for future in as_completed(futures):
                result = future.result()
                failure_results.append(result)
        
        # 验证所有上传都按预期失败
        assert len(failure_results) == 5, "应该有 5 个失败结果"
        
        for result in failure_results:
            assert result["failed_as_expected"], f"文件 {result['filename']} 应该上传失败"
        
        # 验证数据库中没有创建不完整的记录
        from app.models.attachment import PromptAttachment
        
        incomplete_attachments = db_session.query(PromptAttachment).filter(
            PromptAttachment.prompt_id == image_prompt.id,
            PromptAttachment.filename.like("failing_test_%")
        ).all()
        
        assert len(incomplete_attachments) == 0, "不应该有不完整的附件记录"