# 認証サービス（Auth Service）ドキュメント

## 目次

1. [概要](#概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [認証フロー](#認証フロー)
4. [API 仕様](#api仕様)
   - [認証関連エンドポイント](#認証関連エンドポイント)
   - [ユーザー管理エンドポイント](#ユーザー管理エンドポイント)
5. [セキュリティ](#セキュリティ)
6. [設定](#設定)
7. [デプロイメント](#デプロイメント)

## 概要

認証サービスは、マイクロサービスアーキテクチャにおけるユーザー認証と認可を担当するコンポーネントです。このサービスは以下の機能を提供します：

- ユーザー登録と管理
- ログイン認証
- JWT トークン発行（アクセストークンとリフレッシュトークン）
- トークン更新
- ログアウト処理

このサービスは FastAPI、PostgreSQL、Redis を使用して実装されています。

## アーキテクチャ

認証サービスは以下のコンポーネントで構成されています：

- **API 層**: FastAPI を使用した RESTful API エンドポイント
- **ビジネスロジック層**: ユーザー認証、トークン管理などのコアロジック
- **データアクセス層**: SQLAlchemy を使用したデータベースアクセス
- **データストレージ**:
  - PostgreSQL: ユーザー情報の永続化
  - Redis: リフレッシュトークンの管理

## 認証フロー

### 登録フロー

1. クライアントがユーザー名とパスワードを`/api/v1/auth/register`エンドポイントに送信
2. サービスがユーザー名の重複をチェック
3. パスワードをハッシュ化してデータベースに保存
4. 新しいユーザー情報をレスポンスとして返却

### ログインフロー

1. クライアントがユーザー名とパスワードを`/api/v1/auth/login`エンドポイントに送信
2. サービスがユーザー名とパスワードを検証
3. 検証成功時、アクセストークンとリフレッシュトークンを生成
   - アクセストークン: RS256 アルゴリズムを使用した JWT（有効期限: 30 分）
   - リフレッシュトークン: Redis に保存されるランダムトークン（有効期限: 7 日）
4. トークンをレスポンスとして返却

### トークン更新フロー

1. クライアントがリフレッシュトークンを`/api/v1/auth/refresh`エンドポイントに送信
2. サービスがリフレッシュトークンを検証
3. 検証成功時、古いリフレッシュトークンを無効化
4. 新しいアクセストークンとリフレッシュトークンを生成
5. 新しいトークンをレスポンスとして返却

### ログアウトフロー

1. クライアントがリフレッシュトークンを`/api/v1/auth/logout`エンドポイントに送信
2. サービスがリフレッシュトークンを Redis から削除（無効化）
3. 成功メッセージをレスポンスとして返却

## API 仕様

ベース URL: `/api/v1`

### 認証関連エンドポイント

#### ユーザー登録

```
POST /auth/register
```

**説明**: 新しい一般ユーザーを登録します。

**認証要件**: 不要

**リクエストボディ**:

```json
{
  "username": "string", // 必須、1-50文字
  "password": "string" // 必須、1-16文字
}
```

**レスポンス** (200 OK):

```json
{
  "id": "uuid",
  "username": "string",
  "is_admin": false,
  "is_active": true
}
```

**エラーレスポンス**:

- 400 Bad Request: ユーザー名が既に使用されている
- 422 Unprocessable Entity: リクエストボディが無効
- 500 Internal Server Error: サーバーエラー

---

#### 管理者によるユーザー登録

```
POST /auth/admin/register
```

**説明**: 管理者が新しいユーザーを登録します。管理者権限を持つユーザーを作成することも可能です。

**認証要件**: 管理者権限を持つユーザーのアクセストークン

**リクエストボディ**:

```json
{
  "username": "string",  // 必須、1-50文字
  "password": "string",  // 必須、1-16文字
  "is_admin": boolean    // オプション、デフォルトはfalse
}
```

**レスポンス** (200 OK):

```json
{
  "id": "uuid",
  "username": "string",
  "is_admin": boolean,
  "is_active": true
}
```

**エラーレスポンス**:

- 400 Bad Request: ユーザー名が既に使用されている
- 401 Unauthorized: 認証情報が無効
- 403 Forbidden: 管理者権限がない
- 422 Unprocessable Entity: リクエストボディが無効
- 500 Internal Server Error: サーバーエラー

---

#### ログイン

```
POST /auth/login
```

**説明**: ユーザー認証を行い、アクセストークンとリフレッシュトークンを発行します。

**認証要件**: 不要

**リクエストボディ** (application/x-www-form-urlencoded):

```
username: string  // 必須
password: string  // 必須
```

**レスポンス** (200 OK):

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

**エラーレスポンス**:

- 401 Unauthorized: ユーザー名またはパスワードが正しくない
- 422 Unprocessable Entity: リクエストボディが無効

---

#### トークン更新

```
POST /auth/refresh
```

**説明**: リフレッシュトークンを使用して新しいアクセストークンとリフレッシュトークンを発行します。

**認証要件**: 不要

**リクエストボディ**:

```json
{
  "refresh_token": "string" // 必須
}
```

**レスポンス** (200 OK):

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

**エラーレスポンス**:

- 401 Unauthorized: リフレッシュトークンが無効
- 422 Unprocessable Entity: リクエストボディが無効

---

#### ログアウト

```
POST /auth/logout
```

**説明**: リフレッシュトークンを無効化してログアウトします。

**認証要件**: 不要

**リクエストボディ**:

```json
{
  "refresh_token": "string" // 必須
}
```

**レスポンス** (200 OK):

```json
{
  "detail": "ログアウトしました"
}
```

**エラーレスポンス**:

- 400 Bad Request: 無効なトークン
- 422 Unprocessable Entity: リクエストボディが無効

### ユーザー管理エンドポイント

#### 全ユーザー取得

```
GET /auth/users
```

**説明**: 全てのユーザー情報を取得します。

**認証要件**: 管理者権限を持つユーザーのアクセストークン

**レスポンス** (200 OK):

```json
[
  {
    "id": "uuid",
    "username": "string",
    "is_admin": boolean,
    "is_active": boolean
  }
]
```

**エラーレスポンス**:

- 401 Unauthorized: 認証情報が無効
- 403 Forbidden: 管理者権限がない

---

#### ユーザー情報取得

```
GET /auth/user/{user_id}
```

**説明**: 指定されたユーザーの情報を取得します。自分自身または管理者のみが取得可能です。

**パスパラメータ**:

- `user_id`: 取得対象のユーザー ID (UUID)

**認証要件**: 有効なアクセストークン

**レスポンス** (200 OK):

```json
{
  "id": "uuid",
  "username": "string",
  "is_admin": boolean,
  "is_active": boolean
}
```

**エラーレスポンス**:

- 401 Unauthorized: 認証情報が無効
- 403 Forbidden: 権限がない
- 404 Not Found: 指定されたユーザーが存在しない

---

#### ユーザー情報更新

```
PUT /auth/update/user/{user_id}
```

**説明**: 指定されたユーザーの情報を更新します。自分自身または管理者のみが更新可能です。管理者権限の変更は管理者のみが可能です。

**パスパラメータ**:

- `user_id`: 更新対象のユーザー ID (UUID)

**認証要件**: 有効なアクセストークン

**リクエストボディ**:

```json
{
  "username": "string",    // オプション、最大50文字
  "password": "string",    // オプション、最大16文字
  "is_active": boolean,    // オプション
  "is_admin": boolean      // オプション、管理者のみ変更可能
}
```

**レスポンス** (200 OK):

```json
{
  "id": "uuid",
  "username": "string",
  "is_admin": boolean,
  "is_active": boolean
}
```

**エラーレスポンス**:

- 400 Bad Request: ユーザー名が既に使用されている
- 401 Unauthorized: 認証情報が無効
- 403 Forbidden: 権限がない
- 404 Not Found: 指定されたユーザーが存在しない
- 422 Unprocessable Entity: リクエストボディが無効
- 500 Internal Server Error: サーバーエラー

---

#### ユーザー削除

```
DELETE /auth/delete/user/{user_id}
```

**説明**: 指定されたユーザーを削除します。管理者のみが実行可能で、自分自身は削除できません。

**パスパラメータ**:

- `user_id`: 削除対象のユーザー ID (UUID)

**認証要件**: 管理者権限を持つユーザーのアクセストークン

**レスポンス** (204 No Content):
コンテンツなし

**エラーレスポンス**:

- 400 Bad Request: 自分自身を削除しようとした
- 401 Unauthorized: 認証情報が無効
- 403 Forbidden: 管理者権限がない
- 404 Not Found: 指定されたユーザーが存在しない
- 500 Internal Server Error: サーバーエラー

## セキュリティ

### 認証方式

- **パスワード**: bcrypt アルゴリズムを使用してハッシュ化
- **アクセストークン**: RS256 アルゴリズム（非対称暗号）を使用した JWT
- **リフレッシュトークン**: Redis に保存されるランダムトークン

### トークンセキュリティ

- アクセストークンの有効期限は 30 分（設定可能）
- リフレッシュトークンの有効期限は 7 日（設定可能）
- ログアウト時にリフレッシュトークンを無効化
- トークン更新時に古いリフレッシュトークンを無効化

### 権限管理

- 一般ユーザーと管理者ユーザーの 2 種類の権限レベル
- 管理者のみが実行できる操作:
  - 管理者権限を持つユーザーの作成
  - 全ユーザー情報の取得
  - 他のユーザーの管理者権限の変更
  - ユーザーの削除

## 設定

設定は環境変数または`.env`ファイルで指定できます。主な設定項目は以下の通りです：

### 環境設定

- `ENVIRONMENT`: 実行環境（development, testing, production）

### ロギング設定

- `LOG_LEVEL`: ログレベル（INFO, DEBUG, WARNING, ERROR, CRITICAL）
- `LOG_TO_FILE`: ファイルへのログ出力有無
- `LOG_FILE_PATH`: ログファイルのパス

### 初期管理者ユーザー設定

- `INITIAL_ADMIN_USERNAME`: 初期管理者ユーザー名
- `INITIAL_ADMIN_PASSWORD`: 初期管理者パスワード

### データベース設定

- `POSTGRES_USER`: PostgreSQL ユーザー名
- `POSTGRES_PASSWORD`: PostgreSQL パスワード
- `POSTGRES_HOST`: PostgreSQL ホスト
- `POSTGRES_PORT`: PostgreSQL ポート
- `POSTGRES_DB`: PostgreSQL データベース名

### Redis 設定

- `REDIS_HOST`: Redis ホスト
- `REDIS_PORT`: Redis ポート

### トークン設定

- `SECRET_KEY`: 対称暗号用の秘密鍵（レガシーサポート用）
- `ALGORITHM`: 署名アルゴリズム（RS256 推奨）
- `PRIVATE_KEY_PATH`: 秘密鍵のパス
- `PUBLIC_KEY_PATH`: 公開鍵のパス
- `ACCESS_TOKEN_EXPIRE_MINUTES`: アクセストークンの有効期限（分）
- `REFRESH_TOKEN_EXPIRE_DAYS`: リフレッシュトークンの有効期限（日）

## デプロイメント

認証サービスは Docker を使用してコンテナ化されています。以下のコマンドでデプロイできます：

```bash
# 単体でデプロイ
cd auth-service
docker-compose up -d

# マイクロサービス全体でデプロイ
cd /path/to/microservice
docker-compose up -d
```

### 前提条件

- Docker と Docker Compose がインストールされていること
- 秘密鍵と公開鍵が `keys/` ディレクトリに配置されていること
- `.env` ファイルが適切に設定されていること
