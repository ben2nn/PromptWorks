"""
版本管理功能测试
"""

import pytest
from app.__version__ import get_version, get_version_info, VERSION_HISTORY


def test_get_version():
    """测试获取版本号"""
    version = get_version()
    assert isinstance(version, str)
    assert len(version.split('.')) == 3  # 确保是 x.y.z 格式


def test_get_version_info():
    """测试获取版本信息元组"""
    version_info = get_version_info()
    assert isinstance(version_info, tuple)
    assert len(version_info) == 3
    assert all(isinstance(part, int) for part in version_info)


def test_version_history():
    """测试版本历史记录"""
    assert isinstance(VERSION_HISTORY, dict)
    current_version = get_version()
    assert current_version in VERSION_HISTORY


def test_version_consistency():
    """测试版本一致性"""
    version = get_version()
    version_info = get_version_info()
    
    # 将版本字符串转换为元组进行比较
    version_parts = tuple(int(part) for part in version.split('.'))
    assert version_parts == version_info