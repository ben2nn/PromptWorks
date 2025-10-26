"""文件验证服务

提供文件类型、大小和安全性验证功能。
"""

import mimetypes
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile

from app.core.config import settings
from app.models.prompt import MediaType


class FileValidationService:
    """文件验证服务
    
    负责验证上传文件的类型、大小和安全性。
    """
    
    # 支持的 MIME 类型映射
    SUPPORTED_MIME_TYPES = {
        MediaType.IMAGE: {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
            'image/webp', 'image/bmp', 'image/tiff'
        },
        MediaType.DOCUMENT: {
            'application/pdf', 'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain', 'text/csv', 'text/markdown'
        },
        MediaType.AUDIO: {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 
            'audio/mp4', 'audio/aac', 'audio/flac'
        },
        MediaType.VIDEO: {
            'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 
            'video/webm', 'video/mkv', 'video/flv'
        }
    }
    
    # 文件头魔数检测（用于安全验证）
    FILE_SIGNATURES = {
        # 图片格式
        b'\xFF\xD8\xFF': 'image/jpeg',
        b'\x89PNG\r\n\x1a\n': 'image/png',
        b'GIF87a': 'image/gif',
        b'GIF89a': 'image/gif',
        b'RIFF': 'image/webp',  # 需要进一步检查
        b'BM': 'image/bmp',
        
        # 文档格式
        b'%PDF': 'application/pdf',
        b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'application/msword',  # DOC/XLS/PPT
        b'PK\x03\x04': 'application/zip',  # DOCX/XLSX/PPTX (ZIP-based)
        
        # 音频格式
        b'ID3': 'audio/mpeg',
        b'\xFF\xFB': 'audio/mpeg',
        b'\xFF\xF3': 'audio/mpeg',
        b'\xFF\xF2': 'audio/mpeg',
        b'RIFF': 'audio/wav',  # 需要进一步检查
        b'OggS': 'audio/ogg',
        
        # 视频格式
        b'\x00\x00\x00\x18ftypmp4': 'video/mp4',
        b'\x00\x00\x00\x20ftypmp4': 'video/mp4',
        b'RIFF': 'video/avi',  # 需要进一步检查
    }
    
    def __init__(self):
        self.max_file_size = settings.FILE_MAX_SIZE
    
    def validate_file_size(self, file_size: int) -> tuple[bool, str | None]:
        """验证文件大小
        
        Args:
            file_size: 文件大小（字节）
            
        Returns:
            tuple[是否有效, 错误信息]
        """
        if file_size <= 0:
            return False, "文件大小无效"
        
        if file_size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"文件大小超过限制，最大允许 {max_mb:.1f}MB，实际 {actual_mb:.1f}MB"
        
        return True, None
    
    def detect_mime_type(self, filename: str, content: bytes | None = None) -> str:
        """检测文件的 MIME 类型
        
        Args:
            filename: 文件名
            content: 文件内容（可选，用于更准确的检测）
            
        Returns:
            检测到的 MIME 类型
        """
        # 首先通过文件名检测
        mime_type, _ = mimetypes.guess_type(filename)
        
        # 如果有文件内容，通过文件头进行验证
        if content and len(content) >= 16:
            detected_type = self._detect_by_signature(content)
            if detected_type:
                # 如果文件头检测结果与文件名检测结果不一致，优先使用文件头结果
                if mime_type != detected_type:
                    mime_type = detected_type
        
        return mime_type or 'application/octet-stream'
    
    def _detect_by_signature(self, content: bytes) -> str | None:
        """通过文件头魔数检测文件类型
        
        Args:
            content: 文件内容
            
        Returns:
            检测到的 MIME 类型，如果无法识别则返回 None
        """
        for signature, mime_type in self.FILE_SIGNATURES.items():
            if content.startswith(signature):
                # 对于 RIFF 格式，需要进一步检查
                if signature == b'RIFF' and len(content) >= 12:
                    riff_type = content[8:12]
                    if riff_type == b'WEBP':
                        return 'image/webp'
                    elif riff_type == b'WAVE':
                        return 'audio/wav'
                    elif riff_type == b'AVI ':
                        return 'video/avi'
                
                return mime_type
        
        return None
    
    def validate_mime_type(self, mime_type: str, media_type: MediaType) -> tuple[bool, str | None]:
        """验证 MIME 类型是否与媒体类型匹配
        
        Args:
            mime_type: 检测到的 MIME 类型
            media_type: 期望的媒体类型
            
        Returns:
            tuple[是否有效, 错误信息]
        """
        if media_type == MediaType.TEXT:
            # 文本类型不需要文件上传
            return False, "文本类型不支持文件上传"
        
        supported_types = self.SUPPORTED_MIME_TYPES.get(media_type, set())
        
        if mime_type not in supported_types:
            return False, f"文件类型 {mime_type} 不支持 {media_type.value} 媒体类型"
        
        return True, None
    
    def validate_file_security(self, content: bytes, filename: str) -> tuple[bool, str | None]:
        """验证文件安全性
        
        Args:
            content: 文件内容
            filename: 文件名
            
        Returns:
            tuple[是否安全, 错误信息]
        """
        # 检查文件名安全性
        if not self._is_safe_filename(filename):
            return False, "文件名包含不安全字符"
        
        # 检查文件内容安全性
        if not self._is_safe_content(content):
            return False, "文件内容可能包含恶意代码"
        
        return True, None
    
    def _is_safe_filename(self, filename: str) -> bool:
        """检查文件名是否安全
        
        Args:
            filename: 文件名
            
        Returns:
            是否安全
        """
        # 检查危险字符
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # 检查文件名长度
        if len(filename) > 255:
            return False
        
        # 检查是否为空或只包含空格
        if not filename.strip():
            return False
        
        return True
    
    def _is_safe_content(self, content: bytes) -> bool:
        """检查文件内容是否安全
        
        Args:
            content: 文件内容
            
        Returns:
            是否安全
        """
        # 检查文件大小（防止过大文件）
        if len(content) > self.max_file_size:
            return False
        
        # 检查是否包含可执行文件头
        executable_signatures = [
            b'MZ',  # Windows PE
            b'\x7fELF',  # Linux ELF
            b'\xCA\xFE\xBA\xBE',  # Java class
            b'\xFE\xED\xFA\xCE',  # Mach-O
            b'\xFE\xED\xFA\xCF',  # Mach-O
        ]
        
        for sig in executable_signatures:
            if content.startswith(sig):
                return False
        
        # 检查脚本内容（简单检查）
        script_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'<?php',
            b'#!/bin/',
            b'#!/usr/bin/',
        ]
        
        content_lower = content.lower()
        for pattern in script_patterns:
            if pattern in content_lower:
                return False
        
        return True
    
    async def validate_upload_file(
        self, 
        file: UploadFile, 
        media_type: MediaType
    ) -> tuple[bool, str | None, str | None]:
        """验证上传文件的完整性
        
        Args:
            file: 上传的文件对象
            media_type: 期望的媒体类型
            
        Returns:
            tuple[是否有效, 错误信息, 检测到的MIME类型]
        """
        if not file.filename:
            return False, "文件名不能为空", None
        
        # 读取文件内容
        try:
            content = await file.read()
            # 重置文件指针
            await file.seek(0)
        except Exception as e:
            return False, f"读取文件失败: {str(e)}", None
        
        # 验证文件大小
        is_valid_size, size_error = self.validate_file_size(len(content))
        if not is_valid_size:
            return False, size_error, None
        
        # 检测 MIME 类型
        detected_mime = self.detect_mime_type(file.filename, content)
        
        # 验证 MIME 类型
        is_valid_mime, mime_error = self.validate_mime_type(detected_mime, media_type)
        if not is_valid_mime:
            return False, mime_error, detected_mime
        
        # 验证文件安全性
        is_safe, security_error = self.validate_file_security(content, file.filename)
        if not is_safe:
            return False, security_error, detected_mime
        
        return True, None, detected_mime
    
    def get_supported_extensions(self, media_type: MediaType) -> list[str]:
        """获取指定媒体类型支持的文件扩展名
        
        Args:
            media_type: 媒体类型
            
        Returns:
            支持的文件扩展名列表
        """
        mime_types = self.SUPPORTED_MIME_TYPES.get(media_type, set())
        extensions = []
        
        for mime_type in mime_types:
            # 通过 mimetypes 模块获取扩展名
            exts = mimetypes.guess_all_extensions(mime_type)
            extensions.extend(exts)
        
        # 去重并排序
        return sorted(list(set(extensions)))
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小显示
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化的文件大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# 创建全局实例
file_validation_service = FileValidationService()


__all__ = ["FileValidationService", "file_validation_service"]