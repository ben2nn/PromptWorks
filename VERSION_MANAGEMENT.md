# PromptWorks 版本管理指南

## 概述

PromptWorks 项目实现了统一的版本管理系统，确保前后端版本一致性，并提供便捷的版本更新工具。

## 版本管理架构

### 核心文件
- `app/__version__.py` - 统一版本定义文件
- `pyproject.toml` - 后端项目版本配置
- `frontend/package.json` - 前端项目版本配置
- `scripts/update_version.py` - 版本更新脚本

### API 端点
- `GET /api/v1/system/version` - 获取详细版本信息
- `GET /api/v1/system/health` - 系统健康检查和版本

### 前端组件
- `frontend/src/components/VersionInfo.vue` - 版本显示组件
- `frontend/src/api/system.ts` - 系统 API 调用封装

## 使用方法

### 1. 查看当前版本
```bash
# 通过 Python 代码查看
uv run python -c "from app import get_version; print(f'版本: {get_version()}')"

# 通过演示脚本查看
uv run python demo_version.py
```

### 2. 更新版本号
```bash
# 使用版本更新脚本（推荐）
uv run python scripts/update_version.py 0.2.0

# 验证更新结果
uv run python -c "from app import get_version; print(f'新版本: {get_version()}')"
cd frontend && npm run build
```

### 3. API 调用示例
```bash
# 获取版本信息
curl http://localhost:8000/api/v1/system/version

# 健康检查
curl http://localhost:8000/api/v1/system/health
```

## 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号 (MAJOR)**：不兼容的 API 修改
- **次版本号 (MINOR)**：向下兼容的功能性新增  
- **修订号 (PATCH)**：向下兼容的问题修正

### 版本更新示例
- `0.1.0` → `0.1.1`：修复 bug
- `0.1.0` → `0.2.0`：新增功能
- `0.1.0` → `1.0.0`：重大更新或 API 变更

## 开发工作流

### 版本发布流程
1. 确定版本号类型（patch/minor/major）
2. 运行版本更新脚本
3. 更新版本历史记录（在 `app/__version__.py` 中）
4. 运行测试确保功能正常
5. 提交代码并创建 Git 标签

### 示例命令
```bash
# 1. 更新版本号
uv run python scripts/update_version.py 0.2.0

# 2. 运行测试
uv run poe test-all

# 3. 提交更改
git add .
git commit -m "chore: 更新版本号至 0.2.0"
git tag v0.2.0
git push origin main --tags
```

## 故障排除

### 常见问题

1. **版本不一致**
   - 使用 `scripts/update_version.py` 统一更新所有文件

2. **API 端点无法访问**
   - 确保后端服务正在运行
   - 检查路由配置是否正确

3. **前端版本显示错误**
   - 检查 `frontend/src/api/system.ts` 配置
   - 确认 API 基础地址设置正确

### 调试命令
```bash
# 检查版本一致性
uv run python -c "
from app.__version__ import get_version, get_version_info
import json
with open('frontend/package.json') as f:
    frontend_version = json.load(f)['version']
print(f'后端版本: {get_version()}')
print(f'前端版本: {frontend_version}')
print(f'版本一致: {get_version() == frontend_version}')
"

# 测试 API 端点
uv run python -c "
import httpx
try:
    response = httpx.get('http://localhost:8000/api/v1/system/version')
    print(f'API 响应: {response.json()}')
except Exception as e:
    print(f'API 调用失败: {e}')
"
```

## 最佳实践

1. **始终使用版本更新脚本**，避免手动修改版本号
2. **在发布前运行完整测试套件**，确保版本更新不会破坏功能
3. **为每个版本添加有意义的描述**，便于追踪变更历史
4. **使用 Git 标签标记版本发布**，便于版本回溯
5. **在 CI/CD 流程中集成版本检查**，确保版本一致性