#!/bin/bash
set -e

# マイグレーションの実行
echo "Running database migrations..."
alembic upgrade head

# 環境変数からホストとポートを取得（デフォルト値を設定）
PORT=${POST_SERVICE_INTERNAL_PORT:-"8081"}

# 直接uvicornを実行
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
