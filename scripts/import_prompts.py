#!/usr/bin/env python3
"""
提示词导入脚本
从 JSON 文件导入提示词数据到数据库

使用方法:
    python scripts/import_prompts.py prompts_20251025_192918.json

功能:
    1. 解析 JSON 数据
    2. 优先插入所有唯一的 tags
    3. 下载图片并上传到系统
    4. 插入提示词并关联分类与 tags
    5. 处理中英文提示词内容
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

    def _split_content(self, content: str) -> tuple[str, str | None]:
        """
        分离中英文提示词内容
        
        规则:
        - 如果包含 "=== 提示词 ===" 分隔符，则分为英文和中文
        - 否则，判断内容主要语言
        """
        if "=== 提示词 ===" in content:
            parts = content.split("=== 提示词 ===", 1)
            english = parts[0].strip()
            chinese = parts[1].strip() if len(parts) > 1 else None
            return english, chinese
        
        # 判断是否主要是中文
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        total_chars = len(content.replace(' ', '').replace('\n', ''))
        
        if total_chars > 0 and chinese_chars / total_chars > 0.3:
            # 主要是中文
            return "", content
        else:
            # 主要是英文
            return content, None

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
        """下载图片并上传到系统"""
        try:
            print(f"  → 下载图片: {image_url}")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(image_url, follow_redirects=True)
                response.raise_for_status()
                
                # 获取文件名和扩展名
                parsed_url = urlparse(image_url)
                original_filename = Path(parsed_url.path).name
                
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
                
                print(f"  ✓ 图片已上传: {filename}")
                return attachment
                
        except Exception as e:
            print(f"  ✗ 图片下载失败: {str(e)}")
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
        print(f"\n[{index}/{total}] 导入: {title}")

        # 分离中英文内容
        content = prompt_data.get("content", "")
        english_content, chinese_content = self._split_content(content)

        # 处理标签
        tags = []
        for tag_name in prompt_data.get("tags", []):
            tag = self._ensure_tag(db, tag_name)
            tags.append(tag)

        # 下载并上传图片
        attachment = None
        image_url = prompt_data.get("image_url")
        if image_url:
            attachment = self._download_and_upload_image(
                db, image_url, title
            )

        # 创建提示词
        prompt = Prompt(
            class_id=self.class_id,
            name=title,
            description=f"来源: {prompt_data.get('source_url', 'opennana.com')}",
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
        print(f"    - 标签: {', '.join(tag.name for tag in tags)}")
        if attachment:
            print(f"    - 附件: {attachment.filename}")

    def import_data(self) -> None:
        """执行导入"""
        # 读取 JSON 文件
        print(f"读取文件: {self.json_file}")
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

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
        print("示例: python scripts/import_prompts.py prompts_20251025_192918.json 4")
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
