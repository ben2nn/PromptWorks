"""文件存储服务

提供统一的文件存储接口，支持本地存储和 S3 兼容存储（含 MinIO）。
"""

import os
import uuid
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urljoin

import boto3
from botocore.config import Config as BotoConfig
from fastapi import UploadFile

from app.core.config import settings


class FileStorageService:
    """文件存储服务

    负责处理文件的保存、删除和URL生成等操作。
    支持本地存储和 S3 兼容存储（AWS S3 / MinIO）。
    """

    def __init__(self):
        self.storage_type = settings.FILE_STORAGE_TYPE
        self.storage_path = Path(settings.FILE_STORAGE_PATH)
        self.base_url = settings.FILE_BASE_URL

        if self.storage_type == "s3":
            self._init_s3_client()

        # 确保存储目录存在
        self._ensure_storage_directories()

    def _init_s3_client(self) -> None:
        """初始化 S3 客户端"""
        self.s3_bucket = settings.AWS_S3_BUCKET
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            config=BotoConfig(signature_version="s3v4"),
        )

    def _ensure_storage_directories(self) -> None:
        """确保存储目录结构存在"""
        if self.storage_type == "local":
            # 创建主要目录
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # 创建子目录
            subdirs = ["attachments", "thumbnails", "temp"]
            for subdir in subdirs:
                (self.storage_path / subdir).mkdir(exist_ok=True)

    def _generate_filename(self, original_filename: str) -> str:
        """生成唯一的文件名"""
        file_ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_ext}"

    def _get_file_path(self, filename: str, subdir: str = "attachments") -> Path:
        """获取文件的完整路径"""
        return self.storage_path / subdir / filename

    async def save_file(
        self, file: UploadFile, subdir: str = "attachments"
    ) -> tuple[str, str]:
        """保存文件到存储系统

        Returns:
            tuple[生成的文件名, 文件存储路径]
        """
        filename = self._generate_filename(file.filename or "unknown")
        content = await file.read()

        if self.storage_type == "local":
            file_path = self._get_file_path(filename, subdir)
            try:
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                relative_path = f"{subdir}/{filename}"
                return filename, relative_path
            except Exception as e:
                if file_path.exists():
                    file_path.unlink()
                raise OSError(f"文件保存失败: {str(e)}") from e

        elif self.storage_type == "s3":
            object_key = f"{subdir}/{filename}"
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=object_key,
                    Body=content,
                    ContentType=file.content_type or "application/octet-stream",
                )
                return filename, object_key
            except Exception as e:
                raise OSError(f"S3 文件上传失败: {str(e)}") from e

        raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")

    def save_binary_file(
        self, content: bytes, filename: str, subdir: str = "thumbnails"
    ) -> str:
        """保存二进制内容到文件

        Returns:
            文件存储路径
        """
        if self.storage_type == "local":
            file_path = self._get_file_path(filename, subdir)
            try:
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                return f"{subdir}/{filename}"
            except Exception as e:
                if file_path.exists():
                    file_path.unlink()
                raise OSError(f"文件保存失败: {str(e)}") from e

        elif self.storage_type == "s3":
            object_key = f"{subdir}/{filename}"
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=object_key,
                    Body=content,
                )
                return object_key
            except Exception as e:
                raise OSError(f"S3 文件上传失败: {str(e)}") from e

        raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")

    def delete_file(self, file_path: str) -> bool:
        """从存储系统删除文件"""
        if self.storage_type == "local":
            try:
                full_path = self.storage_path / file_path
                if full_path.exists():
                    full_path.unlink()
                    return True
                return False
            except Exception:
                return False

        elif self.storage_type == "s3":
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=file_path)
                return True
            except Exception:
                return False

        return False

    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        if self.storage_type == "local":
            full_path = self.storage_path / file_path
            return full_path.exists()

        elif self.storage_type == "s3":
            try:
                self.s3_client.head_object(Bucket=self.s3_bucket, Key=file_path)
                return True
            except Exception:
                return False

        return False

    def get_file_url(self, file_path: str) -> str:
        """获取文件访问URL"""
        if self.storage_type == "local":
            return urljoin(self.base_url, f"/api/v1/files/{file_path}")

        elif self.storage_type == "s3":
            # 生成预签名 URL，默认 1 小时有效
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.s3_bucket, "Key": file_path},
                    ExpiresIn=3600,
                )
                return url
            except Exception:
                return ""

        raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")

    def get_file_path(self, file_path: str) -> Path:
        """获取文件的完整系统路径（仅本地存储）"""
        return self.storage_path / file_path

    def get_storage_info(self) -> dict:
        """获取存储系统信息"""
        if self.storage_type == "local":
            total_size = 0
            file_count = 0
            try:
                for root, dirs, files in os.walk(self.storage_path):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.exists():
                            total_size += file_path.stat().st_size
                            file_count += 1
            except Exception:
                pass

            return {
                "storage_type": self.storage_type,
                "storage_path": str(self.storage_path),
                "total_size": total_size,
                "file_count": file_count,
                "available": True,
            }

        elif self.storage_type == "s3":
            try:
                resp = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket, MaxKeys=1
                )
                return {
                    "storage_type": "s3",
                    "bucket": self.s3_bucket,
                    "endpoint": settings.AWS_S3_ENDPOINT_URL or "AWS S3",
                    "available": True,
                }
            except Exception as e:
                return {
                    "storage_type": "s3",
                    "available": False,
                    "error": str(e),
                }

        return {
            "storage_type": self.storage_type,
            "available": False,
            "error": "存储类型暂未实现",
        }


# 创建全局实例
file_storage_service = FileStorageService()


__all__ = ["FileStorageService", "file_storage_service"]
