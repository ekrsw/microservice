# API-Gateway

このディレクトリには、マイクロサービスアーキテクチャのAPI-Gatewayの実装が含まれています。API-GatewayはNginxを使用して実装されており、各マイクロサービスへのリクエストのルーティングを担当します。

## 概要

API-Gatewayは以下の役割を果たします：

- クライアント（フロントエンド）からのリクエストを適切なマイクロサービスにルーティング
- CORSヘッダーの設定
- ヘルスチェックエンドポイントの提供
- マイクロサービス間の独立性の確保

## ディレクトリ構造

```
api-gateway/
├── README.md
├── docker-compose.yml
└── nginx/
    ├── Dockerfile
    ├── nginx.conf
    └── conf.d/
        └── default.conf
```

## 設定ファイル

### docker-compose.yml

このファイルは、API-Gatewayのコンテナを定義します。80ポートを公開し、`microservice_network`という共有ネットワークを使用して他のマイクロサービスと通信します。

### nginx/Dockerfile

NginxのDockerイメージをビルドするためのDockerfileです。Nginx:1.25-alpineをベースイメージとして使用し、設定ファイルをコンテナにコピーします。

### nginx/nginx.conf

Nginxのグローバル設定ファイルです。ワーカープロセス、接続数、ログ形式などの基本設定が含まれています。

### nginx/conf.d/default.conf

Nginxのサーバー設定ファイルです。以下の設定が含まれています：

- ヘルスチェックエンドポイント（`/health`）
- auth-serviceへのプロキシ設定（`/api/v1/auth/`）
- CORSヘッダーの設定

## 使用方法

### 前提条件

- Docker
- Docker Compose

### 起動方法

1. 共有ネットワークを作成します（初回のみ）：

```powershell
docker network create microservice_network
```

2. API-Gatewayを起動します：

```powershell
cd api-gateway
docker-compose up -d
```

### 動作確認

API-Gatewayが正常に起動しているかを確認するには、ヘルスチェックエンドポイントにアクセスします：

```powershell
curl http://localhost/health
```

正常に動作している場合、`OK`という応答が返ります。

## マイクロサービスとの連携

API-Gatewayは、`microservice_network`という共有ネットワークを使用して他のマイクロサービスと通信します。各マイクロサービスは、このネットワークに接続する必要があります。

例えば、auth-serviceのdocker-compose.ymlには以下の設定が必要です：

```yaml
networks:
  auth_network:
    driver: bridge
  microservice_network:
    external: true
```

また、authサービスの設定にも共有ネットワークを追加します：

```yaml
services:
  auth:
    # 既存の設定...
    networks:
      - auth_network
      - microservice_network
```

## ルーティング設定

現在、API-Gatewayは以下のルーティング設定を持っています：

- `/health` → API-Gatewayのヘルスチェックエンドポイント
- `/api/v1/auth/*` → auth-serviceの`/api/v1/auth/*`エンドポイント

新しいマイクロサービスを追加する場合は、`nginx/conf.d/default.conf`ファイルに新しいルーティング設定を追加する必要があります。
