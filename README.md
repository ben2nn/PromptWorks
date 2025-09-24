# PromptWorks 项目总览

PromptWorks 是一个聚焦 Prompt 资产管理与大模型运营的全栈解决方案，仓库内包含 FastAPI 后端与 Vue + Element Plus 前端。平台支持 Prompt 全生命周期管理、模型配置、版本对比与评估实验，为团队提供统一的提示词协作与测试工作台。

## ✨ 核心能力
- **Prompt 管理**：支持创建、迭代版本、标签归类，保留完整审计信息。
- **版本对比**：提供差异视图，快速识别提示词更新带来的内容变化。
- **模型运营**：规划集中管理可用 LLM 服务及调用配额（前端已预留界面）。
- **评估测试**：后端暴露实验执行、指标记录能力，前端留有测试面板入口待后续集成。

## 🧱 技术栈
- **后端**：Python 3.10+、FastAPI、SQLAlchemy、Alembic、Redis、Celery。
- **前端**：Vite、Vue 3（TypeScript）、Vue Router、Element Plus。
- **工具链**：uv 进行依赖与任务管理，PoeThePoet 统一开发命令，pytest + coverage 保证质量。

## 🚀 快速开始
### 0. 环境准备
- Python 3.10+
- Node.js 18+
- PostgreSQL、Redis（生产）；本地快速体验可先启动后端服务默认配置。

### 1. 安装依赖
```bash
# 同步后端依赖（包含开发工具）
uv sync --extra dev

# 安装前端依赖（需在 frontend 目录执行）
cd frontend
npm install
```

### 2. 初始化配置
```bash
# 复制环境变量模板并按需修改数据库、Redis、密钥等
cp .env.example .env

# 迁移数据库结构
uv run alembic upgrade head
```

### 3. 启动服务
```bash
# 启动后端 FastAPI 调试服务
uv run poe server
```

```bash
# 启动前端开发服务器（先进入 frontend 目录，可在新终端运行）
cd frontend
npm run dev -- --host
```
前端默认运行在 `http://127.0.0.1:5173`，后端运行在 `http://127.0.0.1:8000`，API 文档可访问 `/docs`。

### 4. 常用质量校验
```bash
uv run poe format      # 统一代码风格
uv run poe lint        # 类型检查
uv run poe test        # 单元与集成测试
uv run poe test-all    # 顺序执行上述三项
```

```bash
# 构建前端生产版（在 frontend 目录执行）
cd frontend
npm run build
```

## 📁 项目结构
```
backend/
├── alembic/                # 数据库迁移脚本
├── app/                    # FastAPI 应用主体
│   ├── api/                # REST 接口
│   ├── core/               # 配置与通用逻辑
│   ├── db/                 # 数据库会话与初始化
│   ├── models/             # SQLAlchemy 模型
│   ├── schemas/            # Pydantic 序列化模型
│   └── services/           # 业务服务封装
├── frontend/               # Vue 3 前端工程
│   ├── public/
│   ├── src/
│   │   ├── router/         # 路由配置
│   │   ├── types/          # TypeScript 类型定义
│   │   ├── views/          # 页面组件（首页、详情、LLM 管理）
│   │   └── App.vue         # 应用骨架布局
│   └── package.json
├── tests/                  # pytest 用例
├── pyproject.toml          # 构建与任务配置
├── README.md               # 项目说明
└── .env.example            # 环境变量模板
```

## 📡 API 与前端联动
- 后端提供 `/api/v1/prompts`、`/api/v1/test_prompt` 等接口供前端调用，当前前端示例使用本地 mock 数据，可在后续迭代中替换为真实 API。
- Prompt 详情页已预置版本 diff 组件与测试面板，接入接口后可实现端到端的提示词验证闭环。

## 🤝 贡献指南
1. Fork 仓库并新建分支。
2. 开发完成后运行 `uv run poe test-all` 确保质量基线。
3. 提交 Pull Request，并在描述中说明变更范围与验证方式。

欢迎提出 Issue 或改进建议，共建 PromptWorks！
