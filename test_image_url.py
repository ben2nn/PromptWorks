#!/usr/bin/env python3
"""
测试图片 URL 生成的脚本
"""
import os
from pathlib import Path
from urllib.parse import urljoin

# 模拟配置
FILE_BASE_URL = "http://192.168.31.222:8000"
file_path = "thumbnails/6_thumb.png"

# 生成 URL（模拟后端逻辑）
def get_file_url(file_path: str) -> str:
    return urljoin(FILE_BASE_URL, f"/api/v1/files/{file_path}")

# 测试
thumbnail_url = get_file_url(file_path)
print(f"生成的缩略图 URL: {thumbnail_url}")

# 验证是否与期望的 URL 匹配
expected_url = "http://192.168.31.222:8000/api/v1/files/thumbnails/6_thumb.png"
print(f"期望的 URL: {expected_url}")
print(f"URL 匹配: {thumbnail_url == expected_url}")