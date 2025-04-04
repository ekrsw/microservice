FROM python:3.12.9-slim

# 作業ディレクトリの設定
WORKDIR /workdir

# 必要な環境変数を設定
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 依存関係のインストール
COPY ./backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY ./backend /workdir

# 非rootユーザーを作成して実行（セキュリティ向上）
RUN adduser --disabled-password --gecos "" appuser && \
    # ボリュームマウントポイントの所有権を変更
    mkdir -p /workdir/.pytest_cache && \
    chown -R appuser:appuser /workdir

# Uvicornでアプリケーションを起動（ワーカー数を制限）
# 環境変数からホストとポートを取得するようにエントリポイントスクリプトを使用
COPY ./backend/docker/fastapi/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["scripts/entrypoint.sh"]