# PromptWorks 版本信息
# 这是项目的统一版本定义文件

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

# 版本历史
VERSION_HISTORY = {
    "0.1.0": "初始版本 - 基础 Prompt 管理功能",
}

def get_version() -> str:
    """获取当前版本号"""
    return __version__

def get_version_info() -> tuple:
    """获取版本信息元组"""
    return __version_info__