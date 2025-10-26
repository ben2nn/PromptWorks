"""媒体类型管理 API 端点

提供媒体类型的查询和管理功能。
支持获取支持的媒体类型列表、类型统计等功能。
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prompt import Prompt, MediaType

router = APIRouter()


@router.get(
    "/",
    summary="获取支持的媒体类型",
    description="获取系统支持的所有媒体类型列表及其描述信息"
)
def get_media_types() -> list[dict[str, Any]]:
    """获取支持的媒体类型列表"""
    
    media_types = [
        {
            "value": MediaType.TEXT.value,
            "label": "文本",
            "description": "纯文本内容的提示词",
            "icon": "document-text",
            "supported_formats": ["txt", "md"],
            "max_size": None  # 文本类型无大小限制
        },
        {
            "value": MediaType.IMAGE.value,
            "label": "图片",
            "description": "包含图片内容的提示词",
            "icon": "photo",
            "supported_formats": ["jpg", "jpeg", "png", "gif", "webp", "bmp"],
            "max_size": 10 * 1024 * 1024  # 10MB
        },
        {
            "value": MediaType.DOCUMENT.value,
            "label": "文档",
            "description": "包含文档文件的提示词",
            "icon": "document",
            "supported_formats": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv"],
            "max_size": 10 * 1024 * 1024  # 10MB
        },
        {
            "value": MediaType.AUDIO.value,
            "label": "音频",
            "description": "包含音频文件的提示词",
            "icon": "musical-note",
            "supported_formats": ["mp3", "wav", "ogg", "m4a"],
            "max_size": 10 * 1024 * 1024  # 10MB
        },
        {
            "value": MediaType.VIDEO.value,
            "label": "视频",
            "description": "包含视频文件的提示词",
            "icon": "video-camera",
            "supported_formats": ["mp4", "avi", "mov", "wmv", "webm"],
            "max_size": 10 * 1024 * 1024  # 10MB
        }
    ]
    
    return media_types


@router.get(
    "/statistics",
    summary="获取媒体类型统计",
    description="获取各媒体类型的提示词数量统计"
)
def get_media_type_statistics(
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """获取媒体类型统计信息"""
    
    # 查询各媒体类型的提示词数量
    stmt = (
        select(Prompt.media_type, func.count(Prompt.id).label('count'))
        .group_by(Prompt.media_type)
    )
    
    results = db.execute(stmt).all()
    
    # 构建统计结果
    statistics = {}
    total_prompts = 0
    
    for media_type, count in results:
        statistics[media_type.value] = {
            "count": count,
            "percentage": 0  # 稍后计算
        }
        total_prompts += count
    
    # 计算百分比
    for media_type_value in statistics:
        if total_prompts > 0:
            statistics[media_type_value]["percentage"] = round(
                (statistics[media_type_value]["count"] / total_prompts) * 100, 2
            )
    
    # 确保所有媒体类型都有统计数据
    for media_type in MediaType:
        if media_type.value not in statistics:
            statistics[media_type.value] = {
                "count": 0,
                "percentage": 0
            }
    
    return {
        "total_prompts": total_prompts,
        "by_media_type": statistics,
        "most_used": max(statistics.items(), key=lambda x: x[1]["count"])[0] if statistics else None
    }


@router.get(
    "/{media_type}/info",
    summary="获取特定媒体类型信息",
    description="获取指定媒体类型的详细信息和配置"
)
def get_media_type_info(
    media_type: MediaType
) -> dict[str, Any]:
    """获取特定媒体类型的详细信息"""
    
    # 媒体类型配置映射
    type_configs = {
        MediaType.TEXT: {
            "value": MediaType.TEXT.value,
            "label": "文本",
            "description": "纯文本内容的提示词，支持 Markdown 格式",
            "icon": "document-text",
            "supported_formats": ["txt", "md"],
            "max_size": None,
            "validation_rules": {
                "required_content": True,
                "min_length": 1,
                "max_length": 100000
            },
            "features": [
                "支持 Markdown 语法",
                "支持富文本编辑",
                "支持语法高亮",
                "支持实时预览"
            ]
        },
        MediaType.IMAGE: {
            "value": MediaType.IMAGE.value,
            "label": "图片",
            "description": "包含图片内容的提示词，支持多种图片格式",
            "icon": "photo",
            "supported_formats": ["jpg", "jpeg", "png", "gif", "webp", "bmp"],
            "max_size": 10 * 1024 * 1024,
            "validation_rules": {
                "required_content": False,
                "max_width": 4096,
                "max_height": 4096,
                "allowed_mime_types": [
                    "image/jpeg", "image/png", "image/gif", 
                    "image/webp", "image/bmp"
                ]
            },
            "features": [
                "自动生成缩略图",
                "支持图片预览",
                "提取图片元数据",
                "支持多图片上传"
            ]
        },
        MediaType.DOCUMENT: {
            "value": MediaType.DOCUMENT.value,
            "label": "文档",
            "description": "包含文档文件的提示词，支持多种办公文档格式",
            "icon": "document",
            "supported_formats": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv"],
            "max_size": 10 * 1024 * 1024,
            "validation_rules": {
                "required_content": False,
                "allowed_mime_types": [
                    "application/pdf",
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "application/vnd.ms-excel",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-powerpoint",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    "text/plain",
                    "text/csv"
                ]
            },
            "features": [
                "支持文档预览",
                "提取文档元数据",
                "支持多文档上传",
                "文档格式验证"
            ]
        },
        MediaType.AUDIO: {
            "value": MediaType.AUDIO.value,
            "label": "音频",
            "description": "包含音频文件的提示词，支持多种音频格式",
            "icon": "musical-note",
            "supported_formats": ["mp3", "wav", "ogg", "m4a"],
            "max_size": 10 * 1024 * 1024,
            "validation_rules": {
                "required_content": False,
                "max_duration": 600,  # 10分钟
                "allowed_mime_types": [
                    "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4"
                ]
            },
            "features": [
                "音频播放器",
                "提取音频元数据",
                "显示音频时长",
                "音频格式验证"
            ]
        },
        MediaType.VIDEO: {
            "value": MediaType.VIDEO.value,
            "label": "视频",
            "description": "包含视频文件的提示词，支持多种视频格式",
            "icon": "video-camera",
            "supported_formats": ["mp4", "avi", "mov", "wmv", "webm"],
            "max_size": 10 * 1024 * 1024,
            "validation_rules": {
                "required_content": False,
                "max_duration": 600,  # 10分钟
                "max_width": 1920,
                "max_height": 1080,
                "allowed_mime_types": [
                    "video/mp4", "video/avi", "video/mov", 
                    "video/wmv", "video/webm"
                ]
            },
            "features": [
                "视频播放器",
                "生成视频缩略图",
                "提取视频元数据",
                "显示视频时长和分辨率"
            ]
        }
    }
    
    return type_configs.get(media_type, {})


@router.get(
    "/{media_type}/validation-rules",
    summary="获取媒体类型验证规则",
    description="获取指定媒体类型的文件验证规则"
)
def get_media_type_validation_rules(
    media_type: MediaType
) -> dict[str, Any]:
    """获取媒体类型的验证规则"""
    
    info = get_media_type_info(media_type)
    
    return {
        "media_type": media_type.value,
        "validation_rules": info.get("validation_rules", {}),
        "supported_formats": info.get("supported_formats", []),
        "max_size": info.get("max_size"),
        "max_size_mb": info.get("max_size") // (1024 * 1024) if info.get("max_size") else None
    }