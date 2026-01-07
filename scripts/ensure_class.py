#!/usr/bin/env python3
"""
确保分类存在的脚本
如果 opennana 分类不存在，则创建它
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.prompt import PromptClass


def ensure_opennana_class():
    """确保 opennana 分类存在"""
    db = SessionLocal()
    try:
        # 检查分类是否存在
        existing_class = db.query(PromptClass).filter(
            PromptClass.id == 4
        ).first()
        
        if existing_class:
            print(f"✓ 分类已存在:")
            print(f"  ID: {existing_class.id}")
            print(f"  名称: {existing_class.name}")
            print(f"  描述: {existing_class.description}")
            return True
        
        # 创建新分类
        print("→ 创建 opennana 分类...")
        new_class = PromptClass(
            id=4,
            name="opennana",
            description="OpenNana 提示词库 - 来自 opennana.com 的精选 AI 提示词"
        )
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        
        print(f"✓ 分类创建成功:")
        print(f"  ID: {new_class.id}")
        print(f"  名称: {new_class.name}")
        print(f"  描述: {new_class.description}")
        
        return True
        
    except Exception as e:
        print(f"✗ 操作失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def list_all_classes():
    """列出所有分类"""
    db = SessionLocal()
    try:
        classes = db.query(PromptClass).order_by(PromptClass.id).all()
        
        if not classes:
            print("\n当前没有任何分类")
            return
        
        print(f"\n当前所有分类 (共 {len(classes)} 个):")
        print("-" * 60)
        for cls in classes:
            print(f"ID: {cls.id:3d} | 名称: {cls.name:20s} | 提示词数: {len(cls.prompts)}")
            if cls.description:
                print(f"         描述: {cls.description}")
        print("-" * 60)
        
    except Exception as e:
        print(f"✗ 查询失败: {str(e)}")
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("确保 opennana 分类存在")
    print("=" * 60)
    
    # 确保分类存在
    success = ensure_opennana_class()
    
    # 列出所有分类
    list_all_classes()
    
    if success:
        print("\n✅ 准备就绪，可以开始导入数据！")
        print("\n运行导入命令:")
        print("  python scripts/import_prompts.py prompts_20251025_192918.json")
    else:
        print("\n❌ 分类创建失败，请检查数据库连接")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
