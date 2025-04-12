#!/bin/bash
set -e

# マイグレーションの実行
echo "Running database migrations..."
alembic upgrade head

# 環境変数からホストとポートを取得（デフォルト値を設定）
HOST=${API_HOST:-"auth-service"}
PORT=${API_PORT:-"8080"}

# 直接uvicornを実行
exec uvicorn app.main:app --host $HOST --port $PORT --workers 2
