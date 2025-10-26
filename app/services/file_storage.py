"""文件存储服务

提供统一的文件存储接口，支持本地存储和云存储。
"""

import os
import uuid
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urljoin

from fastapi import UploadFile

from app.core.config import settings


class FileStorageService:
    """文件存储服务
    
    负责处理文件的保存、删除和URL生成等操作。
    支持本地存储，为将来扩展云存储预留接口。
    """
    
    def __init__(self):
        self.storage_type = settings.FILE_STORAGE_TYPE
        self.storage_path = Path(settings.FILE_STORAGE_PATH)
        self.base_url = settings.FILE_BASE_URL
        
        # 确保存储目录存在
        self._ensure_storage_directories()
    
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
        """生成唯一的文件名
        
        Args:
            original_filename: 原始文件名
            
        Returns:
            生成的唯一文件名
        """
        # 获取文件扩展名
        file_ext = Path(original_filename).suffix.lower()
        
        # 生成UUID作为文件名
        unique_id = str(uuid.uuid4())
        
        return f"{unique_id}{file_ext}"
    
    def _get_file_path(self, filename: str, subdir: str = "attachments") -> Path:
        """获取文件的完整路径
        
        Args:
            filename: 文件名
            subdir: 子目录名
            
        Returns:
            文件的完整路径
        """
        return self.storage_path / subdir / filename
    
    async def save_file(self, file: UploadFile, subdir: str = "attachments") -> tuple[str, str]:
        """保存文件到存储系统
        
        Args:
            file: 上传的文件对象
            subdir: 存储子目录
            
        Returns:
            tuple[生成的文件名, 文件存储路径]
            
        Raises:
            OSError: 文件保存失败
        """
        if self.storage_type != "local":
            raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")
        
        # 生成唯一文件名
        filename = self._generate_filename(file.filename or "unknown")
        
        # 获取完整路径
        file_path = self._get_file_path(filename, subdir)
        
        try:
            # 保存文件
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # 返回相对路径用于数据库存储
            relative_path = f"{subdir}/{filename}"
            
            return filename, relative_path
            
        except Exception as e:
            # 如果保存失败，清理可能创建的文件
            if file_path.exists():
                file_path.unlink()
            raise OSError(f"文件保存失败: {str(e)}") from e
    
    def save_binary_file(self, content: bytes, filename: str, subdir: str = "thumbnails") -> str:
        """保存二进制内容到文件
        
        Args:
            content: 二进制内容
            filename: 文件名
            subdir: 存储子目录
            
        Returns:
            文件存储路径
            
        Raises:
            OSError: 文件保存失败
        """
        if self.storage_type != "local":
            raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")
        
        # 获取完整路径
        file_path = self._get_file_path(filename, subdir)
        
        try:
            # 保存文件
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # 返回相对路径
            return f"{subdir}/{filename}"
            
        except Exception as e:
            # 如果保存失败，清理可能创建的文件
            if file_path.exists():
                file_path.unlink()
            raise OSError(f"文件保存失败: {str(e)}") from e
    
    def delete_file(self, file_path: str) -> bool:
        """从存储系统删除文件
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            删除是否成功
        """
        if self.storage_type != "local":
            raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")
        
        try:
            full_path = self.storage_path / file_path
            if full_path.exists():
                full_path.unlink()
                return True
            return False
            
        except Exception:
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            文件是否存在
        """
        if self.storage_type != "local":
            raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")
        
        full_path = self.storage_path / file_path
        return full_path.exists()
    
    def get_file_url(self, file_path: str) -> str:
        """获取文件访问URL
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            文件访问URL
        """
        if self.storage_type == "local":
            # 本地存储使用相对URL
            return urljoin(self.base_url, f"/api/v1/files/{file_path}")
        else:
            raise NotImplementedError(f"存储类型 {self.storage_type} 暂未实现")
    
    def get_file_path(self, file_path: str) -> Path:
        """获取文件的完整系统路径
        
        Args:
            file_path: 文件相对路径
            
        Returns:
            文件的完整系统路径
        """
        return self.storage_path / file_path
    
    def get_storage_info(self) -> dict:
        """获取存储系统信息
        
        Returns:
            存储系统信息字典
        """
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
                "available": True
            }
        else:
            return {
                "storage_type": self.storage_type,
                "available": False,
                "error": "存储类型暂未实现"
            }


# 创建全局实例
file_storage_service = FileStorageService()


__all__ = ["FileStorageService", "file_storage_service"]