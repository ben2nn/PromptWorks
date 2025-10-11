#!/usr/bin/env bash
set -euo pipefail

APP_HOST=${APP_HOST:-0.0.0.0}
APP_PORT=${APP_PORT:-8000}

echo "等待数据库迁移..."
until alembic upgrade head; do
  echo "数据库暂未就绪，3 秒后重试..."
  sleep 3
done

echo "启动 FastAPI 服务，监听 ${APP_HOST}:${APP_PORT}"
exec uvicorn app.main:app --host "${APP_HOST}" --port "${APP_PORT}"
