"""缩略图生成服务

提供图片缩略图生成和图片元数据提取功能。
"""

import io
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, ExifTags
from PIL.Image import Resampling

from app.core.config import settings


class ThumbnailService:
    """缩略图生成服务
    
    负责为图片生成缩略图并提取图片元数据。
    """
    
    def __init__(self):
        # 解析缩略图尺寸配置
        size_str = settings.THUMBNAIL_SIZE
        if 'x' in size_str:
            width, height = map(int, size_str.split('x'))
            self.thumbnail_size = (width, height)
        else:
            # 如果配置格式不正确，使用默认值
            self.thumbnail_size = (200, 200)
        
        self.thumbnail_quality = settings.THUMBNAIL_QUALITY
    
    def is_image_file(self, mime_type: str) -> bool:
        """检查是否为支持的图片格式
        
        Args:
            mime_type: MIME 类型
            
        Returns:
            是否为支持的图片格式
        """
        supported_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
            'image/webp', 'image/bmp', 'image/tiff'
        }
        return mime_type in supported_types
    
    def extract_image_metadata(self, image_content: bytes) -> dict[str, Any]:
        """提取图片元数据
        
        Args:
            image_content: 图片二进制内容
            
        Returns:
            图片元数据字典
        """
        metadata = {}
        
        try:
            with Image.open(io.BytesIO(image_content)) as img:
                # 基本信息
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['format'] = img.format
                metadata['mode'] = img.mode
                
                # 文件大小
                metadata['file_size'] = len(image_content)
                
                # EXIF 信息（如果存在）
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        # 只保留常用的 EXIF 信息
                        if tag in ['DateTime', 'Make', 'Model', 'Software', 'Orientation']:
                            exif_data[tag] = str(value)
                
                if exif_data:
                    metadata['exif'] = exif_data
                
                # 计算宽高比
                if img.height > 0:
                    metadata['aspect_ratio'] = round(img.width / img.height, 2)
                
                # 判断图片方向
                if img.width > img.height:
                    metadata['orientation'] = 'landscape'  # 横向
                elif img.width < img.height:
                    metadata['orientation'] = 'portrait'   # 纵向
                else:
                    metadata['orientation'] = 'square'     # 正方形
                
        except Exception as e:
            metadata['error'] = f"元数据提取失败: {str(e)}"
        
        return metadata
    
    def generate_thumbnail(self, image_content: bytes, output_format: str = 'JPEG') -> bytes:
        """生成缩略图
        
        Args:
            image_content: 原始图片二进制内容
            output_format: 输出格式 (JPEG, PNG, WEBP)
            
        Returns:
            缩略图二进制内容
            
        Raises:
            ValueError: 图片处理失败
        """
        try:
            with Image.open(io.BytesIO(image_content)) as img:
                # 自动旋转图片（根据 EXIF 信息）
                img = ImageOps.exif_transpose(img)
                
                # 转换为 RGB 模式（如果需要）
                if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # 生成缩略图（保持宽高比）
                img.thumbnail(self.thumbnail_size, Resampling.LANCZOS)
                
                # 保存到内存
                output = io.BytesIO()
                
                # 设置保存参数
                save_kwargs = {}
                if output_format == 'JPEG':
                    save_kwargs['quality'] = self.thumbnail_quality
                    save_kwargs['optimize'] = True
                elif output_format == 'PNG':
                    save_kwargs['optimize'] = True
                elif output_format == 'WEBP':
                    save_kwargs['quality'] = self.thumbnail_quality
                    save_kwargs['method'] = 6  # 最佳压缩
                
                img.save(output, format=output_format, **save_kwargs)
                
                return output.getvalue()
                
        except Exception as e:
            raise ValueError(f"缩略图生成失败: {str(e)}") from e
    
    def get_optimal_thumbnail_format(self, original_mime_type: str) -> tuple[str, str]:
        """获取最优的缩略图格式
        
        Args:
            original_mime_type: 原始图片的 MIME 类型
            
        Returns:
            tuple[PIL格式名, 文件扩展名]
        """
        # 根据原始格式选择最优的缩略图格式
        if original_mime_type in ['image/png', 'image/gif']:
            # PNG 和 GIF 可能有透明度，保持 PNG 格式
            return 'PNG', '.png'
        elif original_mime_type == 'image/webp':
            # WebP 格式保持 WebP
            return 'WEBP', '.webp'
        else:
            # 其他格式转换为 JPEG（更小的文件大小）
            return 'JPEG', '.jpg'
    
    def create_thumbnail_filename(self, original_filename: str, thumbnail_format: str) -> str:
        """创建缩略图文件名
        
        Args:
            original_filename: 原始文件名
            thumbnail_format: 缩略图格式扩展名
            
        Returns:
            缩略图文件名
        """
        # 获取原始文件名（不含扩展名）
        name_without_ext = Path(original_filename).stem
        
        # 添加缩略图后缀和新扩展名
        return f"{name_without_ext}_thumb{thumbnail_format}"
    
    def process_image(self, image_content: bytes, original_filename: str, mime_type: str) -> tuple[bytes, str, dict]:
        """处理图片：生成缩略图和提取元数据
        
        Args:
            image_content: 图片二进制内容
            original_filename: 原始文件名
            mime_type: MIME 类型
            
        Returns:
            tuple[缩略图内容, 缩略图文件名, 图片元数据]
            
        Raises:
            ValueError: 图片处理失败
        """
        if not self.is_image_file(mime_type):
            raise ValueError(f"不支持的图片格式: {mime_type}")
        
        # 提取元数据
        metadata = self.extract_image_metadata(image_content)
        
        # 获取最优缩略图格式
        thumbnail_format, thumbnail_ext = self.get_optimal_thumbnail_format(mime_type)
        
        # 生成缩略图
        thumbnail_content = self.generate_thumbnail(image_content, thumbnail_format)
        
        # 创建缩略图文件名
        thumbnail_filename = self.create_thumbnail_filename(original_filename, thumbnail_ext)
        
        # 添加缩略图信息到元数据
        metadata['thumbnail'] = {
            'width': self.thumbnail_size[0],
            'height': self.thumbnail_size[1],
            'format': thumbnail_format,
            'size': len(thumbnail_content)
        }
        
        return thumbnail_content, thumbnail_filename, metadata
    
    def get_image_info(self, image_content: bytes) -> dict[str, Any]:
        """获取图片基本信息（不生成缩略图）
        
        Args:
            image_content: 图片二进制内容
            
        Returns:
            图片基本信息
        """
        try:
            with Image.open(io.BytesIO(image_content)) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size': len(image_content)
                }
        except Exception as e:
            return {'error': f"图片信息获取失败: {str(e)}"}
    
    def validate_image_content(self, image_content: bytes) -> tuple[bool, str | None]:
        """验证图片内容是否有效
        
        Args:
            image_content: 图片二进制内容
            
        Returns:
            tuple[是否有效, 错误信息]
        """
        try:
            with Image.open(io.BytesIO(image_content)) as img:
                # 尝试验证图片
                img.verify()
            
            # 重新打开进行基本检查
            with Image.open(io.BytesIO(image_content)) as img:
                if img.width <= 0 or img.height <= 0:
                    return False, "图片尺寸无效"
                
                if img.width > 10000 or img.height > 10000:
                    return False, "图片尺寸过大"
            
            return True, None
            
        except Exception as e:
            return False, f"图片验证失败: {str(e)}"


# 创建全局实例
thumbnail_service = ThumbnailService()


__all__ = ["ThumbnailService", "thumbnail_service"]