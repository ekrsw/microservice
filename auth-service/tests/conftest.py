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

from app.db.base import Base
from sqlalchemy.ext.asyncio import AsyncSession # 追加
from app.db.session import test_async_engine, TestAsyncSessionLocal, get_db # get_test_db は不要になるので削除
from app.crud.user import user
from app.main import app
from app.schemas.user import UserCreate, AdminUserCreate
from app.core.config import settings


# テスト用の鍵パスを設定
TEST_PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), "keys/test_private.pem")
TEST_PUBLIC_KEY_PATH = os.path.join(os.path.dirname(__file__), "keys/test_public.pem")

@pytest.fixture(scope="session", autouse=True)
def override_settings():
    """テスト用の設定をオーバーライド"""
    # 元の設定を保存
    original_algorithm = settings.ALGORITHM
    original_private_key_path = settings.PRIVATE_KEY_PATH
    original_public_key_path = settings.PUBLIC_KEY_PATH
    
    # テスト用の設定に変更
    settings.ALGORITHM = "RS256"
    settings.PRIVATE_KEY_PATH = TEST_PRIVATE_KEY_PATH
    settings.PUBLIC_KEY_PATH = TEST_PUBLIC_KEY_PATH
    
    yield
    
    # テスト後に元の設定に戻す
    settings.ALGORITHM = original_algorithm
    settings.PRIVATE_KEY_PATH = original_private_key_path
    settings.PUBLIC_KEY_PATH = original_public_key_path

@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession): # db_session をパラメータとして注入
    """
    非同期テストクライアントを提供し、APIがテストセッションを使用するように依存関係をオーバーライドする
    """
    # db_sessionフィクスチャから提供されたセッションを返す依存関係オーバーライド関数
    async def override_get_db():
        yield db_session # 注入された db_session を返す

    # get_dbの依存関係をオーバーライド
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # テスト後に依存関係をリセット
    del app.dependency_overrides[get_db]


@pytest.fixture
def unique_username():
    """ユニークなユーザー名を生成する"""
    return f"user_{uuid.uuid4()}"

@pytest_asyncio.fixture
async def test_user(db_session, unique_username):
    """テスト用の一般ユーザーを作成する"""
    username = unique_username
    password = "test_password123"
    user_in = UserCreate(
        username=username,
        password=password
    )
    db_user = await user.create(db_session, user_in)
    return db_user

@pytest_asyncio.fixture
async def admin_user(db_session, unique_username):
    """テスト用の管理者ユーザーを作成する"""
    username = f"admin_{unique_username}"
    password = "admin_pass123"  # 16文字以下に短縮
    user_in = AdminUserCreate(
        username=username,
        password=password,
        is_admin=True
    )
    db_user = await user.create(db_session, user_in)
    return db_user

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    # テスト用DBのテーブルを作成（初回のみ）
    # Note: スコープを"session"にして初回のみ実行する方が効率的だが、
    #       ここでは各テストでクリーンな状態を保証するために"function"スコープのままにする
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # 既存テーブルを削除
        await conn.run_sync(Base.metadata.create_all) # テーブル再作成
    
    # テストセッションとネストされたトランザクションを提供
    async with TestAsyncSessionLocal() as session:
        # ネストされたトランザクションを開始
        async with session.begin_nested() as nested_transaction:
            yield session # テスト関数にセッションを提供
            # テスト終了後、ネストされたトランザクションをロールバック
            await nested_transaction.rollback()
        # セッション自体は TestAsyncSessionLocal のコンテキストマネージャが閉じる
