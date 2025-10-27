# 多阶段构建 - 构建阶段
FROM node:20-alpine AS build

WORKDIR /app

# 复制 package 文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm ci

# 复制项目文件
COPY . .

# 构建参数 - API 基础 URL
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

# 构建 Next.js 应用
RUN npm run build

# 生产阶段
FROM node:20-alpine AS production

WORKDIR /app

# 设置环境为生产
ENV NODE_ENV=production

# 复制 package 文件
COPY package.json package-lock.json ./

# 只安装生产依赖
RUN npm ci --only=production

# 从构建阶段复制构建产物
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/next.config.js ./

# 暴露端口
EXPOSE 80

# 启动应用
CMD ["npm", "start"]
