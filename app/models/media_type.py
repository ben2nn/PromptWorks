from enum import Enum


class MediaType(str, Enum):
    """提示词媒体类型枚举
    
    定义系统支持的媒体类型：
    - TEXT: 纯文本内容
    - IMAGE: 图片内容
    - DOCUMENT: 文档内容
    - AUDIO: 音频内容
    - VIDEO: 视频内容
    """
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"


__all__ = ["MediaType"]