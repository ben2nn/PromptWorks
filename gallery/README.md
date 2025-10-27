# Prompt Gallery - 提示词展示网站

一个简洁美观的提示词展示网站，基于 Next.js 14 开发，完全仿照 OpenNana 提示词画廊的设计和功能。

## 功能特性

- 📱 响应式设计，支持桌面端和移动端
- 🔍 实时搜索提示词
- 🏷️ 标签筛选功能
- 🎨 精美的卡片展示
- ✨ 流畅的动画效果
- 📋 一键复制提示词内容
- 🚀 基于 Next.js 14 App Router
- 🎭 使用 Framer Motion 实现动画
- 💅 Tailwind CSS 样式方案

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **动画**: Framer Motion
- **HTTP 客户端**: Axios
- **UI 组件**: React 18

## 快速开始

### 环境要求

- Node.js 20+
- npm 或 yarn

### 安装依赖

```powershell
npm install
```

### 配置环境变量

复制 `.env.example` 到 `.env.local`：

```powershell
Copy-Item .env.example .env.local
```

编辑 `.env.local` 配置 API 地址：

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 启动开发服务器

```powershell
npm run dev
```

访问 http://localhost:3000

## 可用脚本

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run start` - 启动生产服务器
- `npm run lint` - 运行 ESLint 检查
- `npm run preview` - 构建并预览生产版本
- `npm run docker:build` - 构建 Docker 镜像
- `npm run docker:run` - 运行 Docker 容器

## 项目结构

```
gallery/
├── src/
│   ├── app/              # Next.js App Router 页面
│   ├── components/       # React 组件
│   │   ├── Header.tsx
│   │   ├── TagFilter.tsx
│   │   ├── PromptCard.tsx
│   │   ├── PromptGrid.tsx
│   │   ├── PromptModal.tsx
│   │   └── ui/          # 基础 UI 组件
│   ├── lib/             # 工具函数和 API
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── utils.ts
│   └── hooks/           # 自定义 Hooks
│       └── usePrompts.ts
├── public/              # 静态资源
├── .env.example         # 环境变量示例
├── .env.local           # 本地环境变量
├── next.config.js       # Next.js 配置
├── tailwind.config.ts   # Tailwind CSS 配置
├── Dockerfile           # Docker 配置
└── package.json         # 项目依赖
```

## 部署

详细的部署指南请参考 [DEPLOYMENT.md](./DEPLOYMENT.md)

### Docker 部署

```powershell
# 构建镜像
docker build -t prompt-gallery .

# 运行容器
docker run -p 3000:3000 --env-file .env.local prompt-gallery
```

### Docker Compose 部署

在项目根目录执行：

```powershell
docker-compose up -d gallery
```

## API 接口

项目通过以下 API 接口获取数据：

- `GET /api/v1/gallery/prompts` - 获取提示词列表
- `GET /api/v1/gallery/prompts/:id` - 获取单个提示词详情
- `GET /api/v1/gallery/tags` - 获取标签列表
- `GET /api/v1/gallery/search?q=keyword` - 搜索提示词

## 开发指南

### 添加新组件

在 `src/components/` 目录下创建新组件：

```typescript
// src/components/MyComponent.tsx
export default function MyComponent() {
  return <div>My Component</div>
}
```

### 添加新页面

在 `src/app/` 目录下创建新页面：

```typescript
// src/app/about/page.tsx
export default function AboutPage() {
  return <div>About Page</div>
}
```

### 使用 API

使用封装好的 API 函数：

```typescript
import { getPrompts, searchPrompts } from '@/lib/api'

const prompts = await getPrompts()
const results = await searchPrompts('keyword')
```

## 性能优化

- ✅ Next.js 自动代码分割
- ✅ 图片自动优化（Next.js Image）
- ✅ 静态资源缓存
- ✅ API 请求缓存
- ✅ 组件懒加载

## 浏览器支持

- Chrome (最新版)
- Firefox (最新版)
- Safari (最新版)
- Edge (最新版)

## 故障排查

### 构建失败

如果遇到构建失败，尝试清理缓存：

```powershell
Remove-Item -Recurse -Force .next
npm run build
```

### API 请求失败

检查环境变量配置是否正确：

```powershell
Get-Content .env.local
```

### 端口被占用

修改端口号：

```powershell
npm run dev -- -p 3001
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 相关链接

- [Next.js 文档](https://nextjs.org/docs)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)
- [Framer Motion 文档](https://www.framer.com/motion/)
- [部署指南](./DEPLOYMENT.md)
