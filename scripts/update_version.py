#!/usr/bin/env python3
"""
版本更新脚本
用于同步更新项目中所有文件的版本号
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List


def update_pyproject_version(version: str) -> None:
    """更新 pyproject.toml 中的版本号"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("警告: pyproject.toml 文件不存在")
        return
    
    content = pyproject_path.read_text(encoding="utf-8")
    # 使用正则表达式替换版本号
    updated_content = re.sub(
        r'version\s*=\s*"[^"]*"',
        f'version = "{version}"',
        content
    )
    
    pyproject_path.write_text(updated_content, encoding="utf-8")
    print(f"✅ 已更新 pyproject.toml 版本号为: {version}")


def update_package_json_version(version: str) -> None:
    """更新前端 package.json 中的版本号"""
    package_json_path = Path("frontend/package.json")
    if not package_json_path.exists():
        print("警告: frontend/package.json 文件不存在")
        return
    
    with open(package_json_path, "r", encoding="utf-8") as f:
        package_data = json.load(f)
    
    package_data["version"] = version
    
    with open(package_json_path, "w", encoding="utf-8") as f:
        json.dump(package_data, f, indent=2, ensure_ascii=False)
        f.write("\n")  # 添加末尾换行符
    
    print(f"✅ 已更新 frontend/package.json 版本号为: {version}")


def update_version_py(version: str) -> None:
    """更新 app/__version__.py 中的版本号"""
    version_py_path = Path("app/__version__.py")
    if not version_py_path.exists():
        print("警告: app/__version__.py 文件不存在")
        return
    
    # 解析版本号为元组
    version_parts = version.split(".")
    if len(version_parts) != 3:
        print(f"错误: 版本号格式不正确，应为 x.y.z 格式，当前为: {version}")
        return
    
    try:
        version_tuple = tuple(int(part) for part in version_parts)
    except ValueError:
        print(f"错误: 版本号包含非数字字符: {version}")
        return
    
    content = version_py_path.read_text(encoding="utf-8")
    
    # 更新 __version__
    content = re.sub(
        r'__version__\s*=\s*"[^"]*"',
        f'__version__ = "{version}"',
        content
    )
    
    # 更新 __version_info__
    content = re.sub(
        r'__version_info__\s*=\s*\([^)]*\)',
        f'__version_info__ = {version_tuple}',
        content
    )
    
    version_py_path.write_text(content, encoding="utf-8")
    print(f"✅ 已更新 app/__version__.py 版本号为: {version}")


def validate_version_format(version: str) -> bool:
    """验证版本号格式是否正确 (x.y.z)"""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python scripts/update_version.py <新版本号>")
        print("示例: python scripts/update_version.py 0.2.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    if not validate_version_format(new_version):
        print(f"错误: 版本号格式不正确，应为 x.y.z 格式，当前为: {new_version}")
        sys.exit(1)
    
    print(f"🚀 开始更新项目版本号为: {new_version}")
    
    # 更新各个文件中的版本号
    update_version_py(new_version)
    update_pyproject_version(new_version)
    update_package_json_version(new_version)
    
    print(f"🎉 版本更新完成! 新版本号: {new_version}")
    print("\n建议执行以下命令验证更新:")
    print("1. uv run python -c \"from app import get_version; print(get_version())\"")
    print("2. cd frontend && npm run build")


if __name__ == "__main__":
    main()