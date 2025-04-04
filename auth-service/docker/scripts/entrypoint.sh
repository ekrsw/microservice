#!/bin/bash
set -e

# 環境変数からホストとポートを取得（デフォルト値を設定）
HOST=${API_HOST:-"0.0.0.0"}
PORT=${API_PORT:-"8000"}

# 直接uvicornを実行
exec uvicorn app.main:app --host $HOST --port $PORT --workers 2
