"""文件存储服务测试

测试文件存储服务的各个功能，包括：
- 文件保存和删除
- URL 生成
- 存储信息统计
- 错误处理
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi import UploadFile

from app.services.file_storage import file_storage_service, FileStorageService


class TestFileStorageService:
    """文件存储服务测试类"""

    @pytest.fixture
    def temp_storage_service(self):
        """创建使用临时目录的存储服务"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = FileStorageService()
            service.storage_path = Path(temp_dir)
            service._ensure_storage_directories()
            yield service

    @pytest.fixture
    def sample_upload_file(self) -> UploadFile:
        """创建测试用的上传文件"""
        content = b"This is test file content."
        file_obj = io.BytesIO(content)
        return UploadFile(
            filename="test_file.txt",
            file=file_obj,
            size=len(content),
            headers={"content-type": "text/plain"}
        )

    def test_ensure_storage_directories(self, temp_storage_service):
        """测试存储目录创建"""
        storage_path = temp_storage_service.storage_path
        
        # 验证主目录存在
        assert storage_path.exists()
        assert storage_path.is_dir()
        
        # 验证子目录存在
        subdirs = ["attachments", "thumbnails", "temp"]
        for subdir in subdirs:
            subdir_path = storage_path / subdir
            assert subdir_path.exists()
            assert subdir_path.is_dir()

    def test_generate_filename(self, temp_storage_service):
        """测试文件名生成"""
        filename1 = temp_storage_service._generate_filename("test.jpg")
        filename2 = temp_storage_service._generate_filename("test.jpg")
        
        # 验证文件名不同（UUID 唯一性）
        assert filename1 != filename2
        
        # 验证扩展名保留
        assert filename1.endswith(".jpg")
        assert filename2.endswith(".jpg")
        
        # 验证没有扩展名的情况
        filename3 = temp_storage_service._generate_filename("test")
        assert not filename3.endswith(".")

    def test_get_file_path(self, temp_storage_service):
        """测试文件路径获取"""
        file_path = temp_storage_service._get_file_path("test.txt", "attachments")
        expected_path = temp_storage_service.storage_path / "attachments" / "test.txt"
        
        assert file_path == expected_path

    async def test_save_file_success(self, temp_storage_service, sample_upload_file):
        """测试成功保存文件"""
        filename, file_path = await temp_storage_service.save_file(
            sample_upload_file, "attachments"
        )
        
        # 验证返回值
        assert filename.endswith(".txt")
        assert file_path == f"attachments/{filename}"
        
        # 验证文件实际保存
        full_path = temp_storage_service.storage_path / file_path
        assert full_path.exists()
        
        # 验证文件内容
        with open(full_path, "rb") as f:
            content = f.read()
        assert content == b"This is test file content."

    async def test_save_file_no_filename(self, temp_storage_service):
        """测试保存没有文件名的文件"""
        content = b"test content"
        file_obj = io.BytesIO(content)
        upload_file = UploadFile(file=file_obj, size=len(content))
        
        filename, file_path = await temp_storage_service.save_file(upload_file)
        
        # 验证使用默认文件名
        assert filename != ""
        assert file_path.startswith("attachments/")

    async def test_save_file_storage_error(self, temp_storage_service):
        """测试文件保存时的存储错误"""
        # 创建一个无效的存储路径
        temp_storage_service.storage_path = Path("/invalid/path/that/does/not/exist")
        
        content = b"test content"
        file_obj = io.BytesIO(content)
        upload_file = UploadFile(filename="test.txt", file=file_obj, size=len(content))
        
        with pytest.raises(OSError, match="文件保存失败"):
            await temp_storage_service.save_file(upload_file)

    def test_save_binary_file_success(self, temp_storage_service):
        """测试成功保存二进制文件"""
        content = b"binary file content"
        filename = "test_binary.bin"
        
        file_path = temp_storage_service.save_binary_file(
            content, filename, "thumbnails"
        )
        
        # 验证返回值
        assert file_path == f"thumbnails/{filename}"
        
        # 验证文件实际保存
        full_path = temp_storage_service.storage_path / file_path
        assert full_path.exists()
        
        # 验证文件内容
        with open(full_path, "rb") as f:
            saved_content = f.read()
        assert saved_content == content

    def test_save_binary_file_storage_error(self, temp_storage_service):
        """测试二进制文件保存时的存储错误"""
        # 创建一个无效的存储路径
        temp_storage_service.storage_path = Path("/invalid/path")
        
        content = b"test content"
        filename = "test.bin"
        
        with pytest.raises(OSError, match="文件保存失败"):
            temp_storage_service.save_binary_file(content, filename)

    def test_delete_file_success(self, temp_storage_service):
        """测试成功删除文件"""
        # 先创建一个文件
        test_file_path = temp_storage_service.storage_path / "attachments" / "test_delete.txt"
        test_file_path.write_text("test content")
        
        # 删除文件
        result = temp_storage_service.delete_file("attachments/test_delete.txt")
        
        assert result is True
        assert not test_file_path.exists()

    def test_delete_file_not_exists(self, temp_storage_service):
        """测试删除不存在的文件"""
        result = temp_storage_service.delete_file("attachments/nonexistent.txt")
        assert result is False

    def test_delete_file_permission_error(self, temp_storage_service):
        """测试删除文件时的权限错误"""
        # 创建一个文件
        test_file_path = temp_storage_service.storage_path / "attachments" / "test_delete.txt"
        test_file_path.write_text("test content")
        
        # 模拟权限错误
        with patch('pathlib.Path.unlink', side_effect=PermissionError("权限不足")):
            result = temp_storage_service.delete_file("attachments/test_delete.txt")
            assert result is False

    def test_file_exists_true(self, temp_storage_service):
        """测试文件存在检查 - 存在"""
        # 创建一个文件
        test_file_path = temp_storage_service.storage_path / "attachments" / "test_exists.txt"
        test_file_path.write_text("test content")
        
        result = temp_storage_service.file_exists("attachments/test_exists.txt")
        assert result is True

    def test_file_exists_false(self, temp_storage_service):
        """测试文件存在检查 - 不存在"""
        result = temp_storage_service.file_exists("attachments/nonexistent.txt")
        assert result is False

    def test_get_file_url_local(self, temp_storage_service):
        """测试获取本地文件 URL"""
        file_path = "attachments/test_file.txt"
        url = temp_storage_service.get_file_url(file_path)
        
        expected_url = f"{temp_storage_service.base_url}/api/v1/files/{file_path}"
        assert url == expected_url

    def test_get_file_url_unsupported_storage(self):
        """测试不支持的存储类型获取 URL"""
        service = FileStorageService()
        service.storage_type = "unsupported"
        
        with pytest.raises(NotImplementedError, match="存储类型 unsupported 暂未实现"):
            service.get_file_url("test/path")

    def test_get_file_path(self, temp_storage_service):
        """测试获取文件完整系统路径"""
        file_path = "attachments/test_file.txt"
        full_path = temp_storage_service.get_file_path(file_path)
        
        expected_path = temp_storage_service.storage_path / file_path
        assert full_path == expected_path

    def test_get_storage_info_local(self, temp_storage_service):
        """测试获取本地存储信息"""
        # 创建一些测试文件
        test_files = [
            ("attachments/file1.txt", "content1"),
            ("attachments/file2.txt", "content2"),
            ("thumbnails/thumb1.jpg", "thumb content"),
        ]
        
        for file_path, content in test_files:
            full_path = temp_storage_service.storage_path / file_path
            full_path.write_text(content)
        
        storage_info = temp_storage_service.get_storage_info()
        
        assert storage_info["storage_type"] == "local"
        assert storage_info["storage_path"] == str(temp_storage_service.storage_path)
        assert storage_info["file_count"] == 3
        assert storage_info["total_size"] > 0
        assert storage_info["available"] is True

    def test_get_storage_info_unsupported(self):
        """测试不支持的存储类型获取存储信息"""
        service = FileStorageService()
        service.storage_type = "unsupported"
        
        storage_info = service.get_storage_info()
        
        assert storage_info["storage_type"] == "unsupported"
        assert storage_info["available"] is False
        assert "error" in storage_info

    def test_get_storage_info_error_handling(self, temp_storage_service):
        """测试获取存储信息时的错误处理"""
        # 模拟文件系统错误
        with patch('os.walk', side_effect=OSError("文件系统错误")):
            storage_info = temp_storage_service.get_storage_info()
            
            # 应该返回基本信息，但统计为 0
            assert storage_info["storage_type"] == "local"
            assert storage_info["total_size"] == 0
            assert storage_info["file_count"] == 0

    def test_not_implemented_storage_type_save_file(self):
        """测试不支持的存储类型保存文件"""
        service = FileStorageService()
        service.storage_type = "s3"  # 未实现的存储类型
        
        content = b"test content"
        file_obj = io.BytesIO(content)
        upload_file = UploadFile(filename="test.txt", file=file_obj, size=len(content))
        
        with pytest.raises(NotImplementedError, match="存储类型 s3 暂未实现"):
            import asyncio
            asyncio.run(service.save_file(upload_file))

    def test_not_implemented_storage_type_save_binary(self):
        """测试不支持的存储类型保存二进制文件"""
        service = FileStorageService()
        service.storage_type = "s3"
        
        with pytest.raises(NotImplementedError, match="存储类型 s3 暂未实现"):
            service.save_binary_file(b"content", "test.bin")

    def test_not_implemented_storage_type_delete_file(self):
        """测试不支持的存储类型删除文件"""
        service = FileStorageService()
        service.storage_type = "s3"
        
        with pytest.raises(NotImplementedError, match="存储类型 s3 暂未实现"):
            service.delete_file("test/path")

    def test_not_implemented_storage_type_file_exists(self):
        """测试不支持的存储类型检查文件存在"""
        service = FileStorageService()
        service.storage_type = "s3"
        
        with pytest.raises(NotImplementedError, match="存储类型 s3 暂未实现"):
            service.file_exists("test/path")

    def test_global_service_instance(self):
        """测试全局服务实例"""
        # 验证全局实例存在且可用
        assert file_storage_service is not None
        assert isinstance(file_storage_service, FileStorageService)
        
        # 验证基本配置
        assert file_storage_service.storage_type in ["local"]
        assert file_storage_service.storage_path is not None

    def test_filename_generation_edge_cases(self, temp_storage_service):
        """测试文件名生成的边界情况"""
        # 测试空文件名
        filename = temp_storage_service._generate_filename("")
        assert filename != ""
        assert not filename.endswith(".")
        
        # 测试只有扩展名的文件名
        filename = temp_storage_service._generate_filename(".txt")
        assert filename.endswith(".txt")
        
        # 测试多个点的文件名
        filename = temp_storage_service._generate_filename("file.name.with.dots.txt")
        assert filename.endswith(".txt")
        
        # 测试大写扩展名
        filename = temp_storage_service._generate_filename("test.JPG")
        assert filename.endswith(".jpg")  # 应该转换为小写

    async def test_file_content_integrity(self, temp_storage_service):
        """测试文件内容完整性"""
        # 创建包含特殊字符的内容
        special_content = b"Test content with special chars: \x00\x01\x02\xff\xfe\xfd"
        file_obj = io.BytesIO(special_content)
        upload_file = UploadFile(
            filename="special_content.bin",
            file=file_obj,
            size=len(special_content)
        )
        
        filename, file_path = await temp_storage_service.save_file(upload_file)
        
        # 验证保存的内容完整性
        full_path = temp_storage_service.storage_path / file_path
        with open(full_path, "rb") as f:
            saved_content = f.read()
        
        assert saved_content == special_content

    def test_concurrent_file_operations(self, temp_storage_service):
        """测试并发文件操作的安全性"""
        import threading
        import time
        
        results = []
        errors = []
        
        def save_file_worker(worker_id):
            try:
                content = f"Worker {worker_id} content".encode()
                filename = f"worker_{worker_id}.txt"
                file_path = temp_storage_service.save_binary_file(
                    content, filename, "temp"
                )
                results.append((worker_id, file_path))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # 启动多个线程同时保存文件
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_file_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0, f"发生错误: {errors}"
        assert len(results) == 5
        
        # 验证所有文件都成功保存
        for worker_id, file_path in results:
            full_path = temp_storage_service.storage_path / file_path
            assert full_path.exists()
            
            with open(full_path, "r") as f:
                content = f.read()
            assert content == f"Worker {worker_id} content"