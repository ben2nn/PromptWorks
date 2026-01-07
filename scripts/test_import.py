#!/usr/bin/env python3
"""
测试导入脚本
用于验证导入功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.prompt import PromptClass, PromptTag


def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    try:
        db = SessionLocal()
        # 简单查询测试
        count = db.query(PromptClass).count()
        print(f"✓ 数据库连接成功，找到 {count} 个分类")
        db.close()
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        return False


def test_class_exists(class_id: int = 4):
    """测试分类是否存在"""
    print(f"\n测试分类 ID {class_id} 是否存在...")
    try:
        db = SessionLocal()
        prompt_class = db.query(PromptClass).filter(
            PromptClass.id == class_id
        ).first()
        
        if prompt_class:
            print(f"✓ 分类存在: {prompt_class.name}")
            db.close()
            return True
        else:
            print(f"✗ 分类 ID {class_id} 不存在")
            print("\n可用的分类:")
            classes = db.query(PromptClass).all()
            for cls in classes:
                print(f"  - ID {cls.id}: {cls.name}")
            db.close()
            return False
    except Exception as e:
        print(f"✗ 查询失败: {str(e)}")
        return False


def test_storage_directory():
    """测试存储目录是否可写"""
    print("\n测试存储目录...")
    from app.core.config import settings
    
    storage_path = Path(settings.FILE_STORAGE_PATH)
    
    # 检查目录是否存在
    if not storage_path.exists():
        print(f"  → 创建存储目录: {storage_path}")
        try:
            storage_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"✗ 创建目录失败: {str(e)}")
            return False
    
    # 检查是否可写
    test_file = storage_path / "test_write.tmp"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"✓ 存储目录可写: {storage_path}")
        return True
    except Exception as e:
        print(f"✗ 存储目录不可写: {str(e)}")
        return False


def test_json_file(json_file: str):
    """测试 JSON 文件是否有效"""
    print(f"\n测试 JSON 文件: {json_file}")
    
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"✗ 文件不存在: {json_file}")
        return False
    
    try:
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        prompts = data.get("prompts", [])
        print(f"✓ JSON 文件有效，包含 {len(prompts)} 个提示词")
        
        # 显示第一个提示词的信息
        if prompts:
            first = prompts[0]
            print(f"\n第一个提示词示例:")
            print(f"  - 标题: {first.get('title', 'N/A')}")
            print(f"  - 标签: {', '.join(first.get('tags', []))}")
            print(f"  - 图片: {first.get('image_url', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"✗ JSON 文件无效: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("导入脚本环境检查")
    print("=" * 60)
    
    # 测试数据库连接
    if not test_database_connection():
        print("\n❌ 数据库连接失败，请检查配置")
        return False
    
    # 测试分类
    class_id = 4
    if len(sys.argv) > 2:
        class_id = int(sys.argv[2])
    
    if not test_class_exists(class_id):
        print(f"\n❌ 分类 ID {class_id} 不存在")
        return False
    
    # 测试存储目录
    if not test_storage_directory():
        print("\n❌ 存储目录不可用")
        return False
    
    # 测试 JSON 文件（如果提供）
    if len(sys.argv) > 1:
        if not test_json_file(sys.argv[1]):
            print("\n❌ JSON 文件无效")
            return False
    
    print("\n" + "=" * 60)
    print("✅ 所有检查通过，可以开始导入！")
    print("=" * 60)
    print("\n运行导入命令:")
    if len(sys.argv) > 1:
        print(f"  python scripts/import_prompts.py {sys.argv[1]} {class_id}")
    else:
        print(f"  python scripts/import_prompts.py <json_file> {class_id}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
