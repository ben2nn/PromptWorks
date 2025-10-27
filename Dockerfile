FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 安装系统依赖，包括图片处理库
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    && rm -rf /var/lib/apt/lists/*

# 预先复制必要文件，加速 Docker 层缓存
COPY pyproject.toml README.md alembic.ini /app/
COPY app /app/app
COPY alembic /app/alembic

# 升级 pip 和 setuptools 到最新版本
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# 创建文件存储目录
RUN mkdir -p /app/uploads/attachments /app/uploads/thumbnails /app/uploads/temp && \
    chmod -R 755 /app/uploads

# 拷贝入口脚本
COPY docker/backend/entrypoint.sh /app/docker/backend/entrypoint.sh
RUN chmod +x /app/docker/backend/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/backend/entrypoint.sh"]
