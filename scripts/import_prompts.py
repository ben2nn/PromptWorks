#!/usr/bin/env python3
"""
提示词导入脚本
从 JSON 文件导入提示词数据到数据库

使用方法:
    python scripts/import_prompts.py prompts_enhanced_20260201_041155.json

功能:
    1. 解析增强版 JSON 数据格式
    2. 优先插入所有唯一的 tags
    3. 下载封面图片并上传到系统
    4. 插入提示词并关联分类与 tags
    5. 处理中英文提示词内容
    6. 支持新的数据结构（id, slug, title, cover_image, english_prompt, chinese_prompt, tags, detail_url）
"""

import json
import re
import sys
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.prompt import Prompt, PromptClass, PromptTag, PromptVersion
from app.models.attachment import PromptAttachment
from app.services.file_storage import file_storage_service
from app.services.thumbnail import thumbnail_service


class PromptImporter:
    """提示词导入器"""

    def __init__(self, json_file: str, class_id: int = 4):
        self.json_file = Path(json_file)
        self.class_id = class_id  # 默认分类 ID: opennana
        self.tag_cache: dict[str, PromptTag] = {}
        self.tag_colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788"
        ]
        self.color_index = 0

    def _get_next_color(self) -> str:
        """获取下一个标签颜色"""
        color = self.tag_colors[self.color_index % len(self.tag_colors)]
        self.color_index += 1
        return color

    def _split_content(self, english_prompt: str, chinese_prompt: str) -> tuple[str, str | None]:
        """
        处理中英文提示词内容
        
        参数:
        - english_prompt: 英文提示词
        - chinese_prompt: 中文提示词
        
        返回:
        - (英文内容, 中文内容)
        """
        # 清理内容
        english_content = english_prompt.strip() if english_prompt else ""
        chinese_content = chinese_prompt.strip() if chinese_prompt else ""
        
        # 如果都为空，返回空值
        if not english_content and not chinese_content:
            return "", None
            
        # 如果只有一个有内容，判断语言
        if not english_content and chinese_content:
            # 判断中文内容是否实际包含英文
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', chinese_content))
            total_chars = len(chinese_content.replace(' ', '').replace('\n', ''))
            
            if total_chars > 0 and chinese_chars / total_chars > 0.3:
                # 主要是中文
                return "", chinese_content
            else:
                # 主要是英文，移到英文字段
                return chinese_content, None
                
        if not chinese_content and english_content:
            # 判断英文内容是否实际包含中文
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', english_content))
            total_chars = len(english_content.replace(' ', '').replace('\n', ''))
            
            if total_chars > 0 and chinese_chars / total_chars > 0.3:
                # 主要是中文，移到中文字段
                return "", english_content
            else:
                # 主要是英文
                return english_content, None
        
        # 两个都有内容，直接返回
        return english_content, chinese_content if chinese_content else None

    def _ensure_tag(self, db: Session, tag_name: str) -> PromptTag:
        """确保标签存在，如果不存在则创建"""
        if tag_name in self.tag_cache:
            return self.tag_cache[tag_name]

        # 查询数据库
        tag = db.query(PromptTag).filter(PromptTag.name == tag_name).first()

        if not tag:
            # 创建新标签
            tag = PromptTag(
                name=tag_name,
                color=self._get_next_color()
            )
            db.add(tag)
            db.flush()
            print(f"  ✓ 创建标签: {tag_name}")

        self.tag_cache[tag_name] = tag
        return tag

    def _download_and_upload_image(
        self, 
        db: Session,
        image_url: str,
        prompt_title: str
    ) -> PromptAttachment | None:
        """下载封面图片并上传到系统"""
        try:
            print(f"  → 下载封面图片: {image_url}")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(image_url, follow_redirects=True)
                response.raise_for_status()
                
                # 获取文件名和扩展名
                parsed_url = urlparse(image_url)
                original_filename = Path(parsed_url.path).name
                
                # 如果没有文件名，使用默认名称
                if not original_filename or '.' not in original_filename:
                    original_filename = f"cover_image.jpg"
                
                # 确定 MIME 类型
                content_type = response.headers.get('content-type', 'image/jpeg')
                
                # 文件内容
                file_content = response.content
                
                # 生成唯一文件名
                ext = Path(original_filename).suffix or '.jpg'
                filename = f"{uuid.uuid4().hex}{ext}"
                
                # 保存原始文件
                file_path = file_storage_service.save_binary_file(
                    file_content, filename, "attachments"
                )
                
                # 初始化附件数据
                thumbnail_path = None
                file_metadata = {}
                
                # 如果是图片，生成缩略图
                if thumbnail_service.is_image_file(content_type):
                    try:
                        thumbnail_content, thumbnail_filename, image_metadata = (
                            thumbnail_service.process_image(
                                file_content, original_filename, content_type
                            )
                        )
                        
                        # 保存缩略图
                        thumbnail_path = file_storage_service.save_binary_file(
                            thumbnail_content, thumbnail_filename, "thumbnails"
                        )
                        
                        file_metadata = image_metadata
                        
                    except Exception as e:
                        file_metadata = {
                            "thumbnail_error": f"缩略图生成失败: {str(e)}"
                        }
                
                # 创建附件记录
                attachment = PromptAttachment(
                    prompt_id=None,  # 稍后关联
                    filename=filename,
                    original_filename=original_filename,
                    file_size=len(file_content),
                    mime_type=content_type,
                    file_path=file_path,
                    thumbnail_path=thumbnail_path,
                    file_metadata=file_metadata
                )
                
                db.add(attachment)
                db.flush()
                
                print(f"  ✓ 封面图片已上传: {filename}")
                return attachment
                
        except Exception as e:
            print(f"  ✗ 封面图片下载失败: {str(e)}")
            return None

    def _import_prompt(
        self,
        db: Session,
        prompt_data: dict[str, Any],
        index: int,
        total: int
    ) -> None:
        """导入单个提示词"""
        title = prompt_data.get("title", "")
        slug = prompt_data.get("slug", "")
        original_id = prompt_data.get("id", 0)
        
        print(f"\n[{index}/{total}] 导入: {title} (ID: {original_id})")

        # 处理中英文内容
        english_prompt = prompt_data.get("english_prompt", "")
        chinese_prompt = prompt_data.get("chinese_prompt", "")
        english_content, chinese_content = self._split_content(english_prompt, chinese_prompt)

        # 如果两个都为空，跳过
        if not english_content and not chinese_content:
            print(f"  ⚠ 跳过: 没有提示词内容")
            return

        # 处理标签
        tags = []
        for tag_name in prompt_data.get("tags", []):
            if tag_name.strip():  # 确保标签名不为空
                tag = self._ensure_tag(db, tag_name.strip())
                tags.append(tag)

        # 下载并上传封面图片
        attachment = None
        cover_image_url = prompt_data.get("cover_image")
        if cover_image_url:
            attachment = self._download_and_upload_image(
                db, cover_image_url, title
            )

        # 构建描述信息
        detail_url = prompt_data.get("detail_url", "")
        description_parts = []
        if slug:
            description_parts.append(f"Slug: {slug}")
        if detail_url:
            description_parts.append(f"来源: {detail_url}")
        if original_id:
            description_parts.append(f"原始ID: {original_id}")
        
        description = " | ".join(description_parts) if description_parts else "来源: opennana.com"

        # 检查是否已存在相同名称的提示词
        existing_prompt = db.query(Prompt).filter(
            Prompt.class_id == self.class_id,
            Prompt.name == title
        ).first()
        
        if existing_prompt:
            print(f"  ⚠ 跳过: 提示词已存在 (ID: {existing_prompt.id})")
            return

        # 创建提示词
        prompt = Prompt(
            class_id=self.class_id,
            name=title,
            description=description,
            author="opennana",
            tags=tags
        )
        db.add(prompt)
        db.flush()

        # 创建版本
        version = PromptVersion(
            prompt_id=prompt.id,
            version="1.0.0",
            content=english_content or chinese_content or "",
            contentzh=chinese_content
        )
        db.add(version)
        db.flush()

        # 设置当前版本
        prompt.current_version_id = version.id

        # 关联附件
        if attachment:
            attachment.prompt_id = prompt.id

        print(f"  ✓ 提示词已创建 (ID: {prompt.id})")
        print(f"    - 英文内容: {'有' if english_content else '无'}")
        print(f"    - 中文内容: {'有' if chinese_content else '无'}")
        print(f"    - 标签: {', '.join(tag.name for tag in tags) if tags else '无'}")
        if attachment:
            print(f"    - 封面图片: {attachment.filename}")
        if slug:
            print(f"    - Slug: {slug}")

    def import_data(self) -> None:
        """执行导入"""
        # 读取 JSON 文件
        print(f"读取文件: {self.json_file}")
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 新格式：直接是提示词数组
        if isinstance(data, list):
            prompts_data = data
        else:
            # 兼容旧格式：包含 prompts 字段的对象
            prompts_data = data.get("prompts", [])
            
        total = len(prompts_data)
        print(f"找到 {total} 个提示词")

        # 验证分类是否存在
        db = SessionLocal()
        try:
            prompt_class = db.query(PromptClass).filter(
                PromptClass.id == self.class_id
            ).first()
            if not prompt_class:
                print(f"错误: 分类 ID {self.class_id} 不存在")
                return

            print(f"目标分类: {prompt_class.name}")
        finally:
            db.close()

        # 导入提示词
        print("\n开始导入...")
        success_count = 0
        error_count = 0

        for index, prompt_data in enumerate(prompts_data, 1):
            db = SessionLocal()
            try:
                self._import_prompt(db, prompt_data, index, total)
                db.commit()
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"  ✗ 导入失败: {str(e)}")
                db.rollback()
            finally:
                db.close()

        # 输出统计
        print(f"\n{'='*60}")
        print(f"导入完成!")
        print(f"  成功: {success_count}")
        print(f"  失败: {error_count}")
        print(f"  总计: {total}")
        print(f"{'='*60}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python scripts/import_prompts.py <json_file> [class_id]")
        print("示例: python scripts/import_prompts.py prompts_enhanced_20260201_041155.json 4")
        sys.exit(1)

    json_file = sys.argv[1]
    class_id = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    if not Path(json_file).exists():
        print(f"错误: 文件不存在: {json_file}")
        sys.exit(1)

    importer = PromptImporter(json_file, class_id)
    importer.import_data()


if __name__ == "__main__":
    main()
