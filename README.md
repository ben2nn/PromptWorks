# PromptWorks 后端服务

PromptWorks 是一个面向 Prompt 工程与 LLM 测试流程的管理平台。本仓库提供基于 FastAPI 的后端服务，负责 Prompt 管理、测试任务编排、模型调用结果存储与评估指标计算等核心能力。

## ✨ 功能概览

- Prompt 版本管理：版本化保存、查询与回滚基础功能。
- 测试任务编排：支持配置模型、参数、重复次数等信息并记录状态。
- 调用结果与指标存储：持久化保存模型输出及解析后的质量指标。
- REST API：提供标准化接口供前端与第三方系统调用。

## 🛠 技术栈

- Python 3.10+
- FastAPI + Pydantic
- SQLAlchemy 2.x + PostgreSQL
- Redis（预留用于任务队列与缓存）
- Celery / 其他任务执行框架（计划中）

## 🚀 快速开始

1. 安装依赖（推荐使用 uv 管理虚拟环境）：

   ```bash
   uv sync
   ```

2. 配置环境变量：复制示例配置并按需修改数据库、Redis、API Key 等信息。

   ```bash
   cp .env.example .env
   ```

3. 初始化数据库：使用 Alembic 应用最新迁移（确保 `.env` 中的 `DATABASE_URL` 指向可访问的 PostgreSQL 实例）。

   ```bash
   uv run alembic upgrade head
   ```

4. 启动开发服务器：

   ```bash
   uv run fastapi dev app/main.py
   ```

服务器启动后可在 http://127.0.0.1:8000 访问，API 文档位于 /api/v1/openapi.json 与 /docs。

## 🗃️ 数据库迁移

- 同步数据库结构：`uv run alembic upgrade head`
- 创建新迁移：`uv run alembic revision --autogenerate -m "add new table"`
- 回滚上一个迁移：`uv run alembic downgrade -1`

所有命令会读取 `.env` 中的 `DATABASE_URL`。在创建新迁移时，请确保目标数据库已处于最新状态，以便 Alembic 能正确比对差异。

## 🧪 运行测试

项目使用 pytest 进行单元测试与接口测试：

```bash
uv run pytest
```

## 🧰 开发辅助命令（PoeThePoet）

为便于统一执行格式化、类型检查与测试，我们在 `pyproject.toml` 中配置了 PoeThePoet 任务：

1. 首次使用前请安装包含开发工具的依赖：

   ```bash
   uv sync --extra dev
   ```

2. 运行常用任务：

   ```bash
   # 仅格式化代码
   uv run poe format

   # 静态类型检查
   uv run poe lint

   # 以 -s -v 参数运行 pytest
   uv run poe test

   # 依次执行格式化、类型检查、测试
   uv run poe test-all
   ```

所有任务都带有中文说明，可通过 `uv run poe -h` 查看当前支持的命令与帮助信息。

测试示例会使用 SQLite 内存数据库，避免对实际数据库造成影响。

## 📁 目录结构

```
backend/
├── app/
│   ├── api/            # REST 路由与请求处理
│   ├── core/           # 配置、常量与通用依赖
│   ├── db/             # 数据库引擎与会话管理
│   ├── models/         # SQLAlchemy 数据模型
│   ├── schemas/        # Pydantic 请求/响应模型
│   └── services/       # 业务服务与任务逻辑 (待实现)
├── alembic/           # Alembic 配置与迁移脚本
│   └── versions/      # 历史迁移文件
├── alembic.ini        # Alembic CLI 配置
├── tests/              # pytest 测试用例
├── pyproject.toml      # 项目依赖与构建配置
├── README.md           # 使用说明
└── .env.example        # 环境变量示例
```

## 🔌 API 概览

- GET /api/v1/prompts：分页查询 Prompt 列表，支持名称/作者模糊搜索。
- POST /api/v1/prompts：创建新 Prompt 版本。
- GET /api/v1/test_prompt：查询测试任务，按状态或 Prompt 筛选。
- POST /api/v1/test_prompt：创建测试任务记录，待后端或任务队列执行。
- GET /api/v1/test_prompt/{id}/results：获取指定任务的执行结果和指标。

## 🧱 数据模型

- Prompt：存放 Prompt 内容及版本信息。
- TestRun：一次模型调用实验的配置与状态。
- Result：单次模型响应及解析数据。
- Metric：与 Result 关联的质量指标。

实体关系如下：Prompt 1 ── N TestRun 1 ── N Result 1 ── N Metric。

## 📦 部署建议

- 使用 Docker Compose 编排 FastAPI、PostgreSQL 与 Redis。
- 结合 Alembic 生成迁移脚本管理数据库结构。
- 引入 Celery/Redis 执行后台任务，结合队列处理批量测试。
- 配置 Prometheus/Grafana 或其他监控工具关注请求延迟与错误率。

## 🤝 贡献指南

1. Fork 仓库并创建主题分支。
2. 完成开发后运行 uv run pytest 确保测试通过。
3. 提交 PR 时描述变更、影响面与验证方式。

欢迎提交 Issue 与改进建议，共同完善 PromptWorks。
