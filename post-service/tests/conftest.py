from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest
import pytest_asyncio
import uuid
import asyncio
import os
from fastapi import FastAPI
from asgi_lifespan import LifespanManager
from httpx import ASGITransport
from datetime import datetime

from app.db.base import Base
from app.db.session import test_async_engine, TestAsyncSessionLocal, get_db, get_test_db
from app.crud.post import post
from app.main import app
from app.schemas.post import PostCreate
from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def override_settings():
    """テスト用の設定をオーバーライド"""
    # 元の設定を保存
    original_algorithm = settings.ALGORITHM
    original_public_key_path = settings.PUBLIC_KEY_PATH
    
    # テスト用の設定に変更
    settings.ALGORITHM = "RS256"
    settings.PUBLIC_KEY_PATH = os.path.join(os.path.dirname(__file__), "keys/test_public.pem")
    
    yield
    
    # テスト後に元の設定に戻す
    settings.ALGORITHM = original_algorithm
    settings.PUBLIC_KEY_PATH = original_public_key_path

@pytest_asyncio.fixture
async def async_client():
    """非同期テストクライアントを提供する"""
    # テスト用DBを使用するように依存関係をオーバーライド
    app.dependency_overrides[get_db] = get_test_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # テスト後に依存関係をリセット
    app.dependency_overrides = {}

@pytest.fixture
def mock_current_user():
    """モックユーザー情報を提供する"""
    user_id = uuid.uuid4()
    return {"user_id": user_id, "payload": {"sub": str(user_id)}}

@pytest_asyncio.fixture
async def db_session():
    """テスト用DBセッションを提供する"""
    # テスト用DBのテーブルを作成
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # テストセッションを提供
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # テスト後にデータをクリアする（同じセッション内で）
            try:
                await session.rollback()  # 保留中のトランザクションをロールバック
                # テーブルのデータをクリア
                for table in reversed(Base.metadata.sorted_tables):
                    await session.execute(table.delete())
                await session.commit()
            except Exception:
                await session.rollback()
                raise

@pytest_asyncio.fixture
async def test_post(db_session, mock_current_user):
    """テスト用の投稿を作成する"""
    post_in = PostCreate(
        title="テスト投稿",
        content="これはテスト投稿の内容です。",
        is_published=True
    )
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    return db_post

@pytest_asyncio.fixture
async def test_unpublished_post(db_session, mock_current_user):
    """テスト用の非公開投稿を作成する"""
    post_in = PostCreate(
        title="非公開テスト投稿",
        content="これは非公開のテスト投稿です。",
        is_published=False
    )
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    return db_post

@pytest.fixture
def mock_jwt_token():
    """モックJWTトークンを提供する"""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.TEST_SIGNATURE"

# テスト用のディレクトリを作成
os.makedirs(os.path.join(os.path.dirname(__file__), "keys"), exist_ok=True)

# テスト用の公開鍵ファイルを作成
@pytest.fixture(scope="session", autouse=True)
def create_test_keys():
    """テスト用の鍵ファイルを作成する"""
    test_public_key_path = os.path.join(os.path.dirname(__file__), "keys/test_public.pem")
    
    # 既に存在する場合は作成しない
    if not os.path.exists(test_public_key_path):
        # テスト用の公開鍵（実際の検証は行わないダミー）
        test_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tRgeLezV6ffAt0gunVTLw7onLRnrq0/IzW7yWR7QkrmBL7jTKEn5u
+qKhbwKfBstIs+bMY2Zkp18gnTxKLxoS2tFczGkPLPgizskuemMghRniWaoLcyeh
kd3qqGElvW/VDL5AaWTg0nLVkjRo9z+40RQzuVaE8AkAFmxZzow3x+VJYKdjykkJ
0iT9wCS0DRTXu269V264Vf/3jvredZiKRkgwlL9xNAwxXFg0x/XFw005UWVRIkdg
cKWTjpBP2dPwVZ4WWC+9aGVd+Gyn1o0CLelf4rEjGoXbAAEgAqeGUxrcIlbjXfbc
mwIDAQAB
-----END PUBLIC KEY-----"""
        
        with open(test_public_key_path, "w") as f:
            f.write(test_public_key)
    
    yield
    
    # テスト後にファイルを削除しない（他のテストで再利用するため）
