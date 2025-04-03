import pytest
import pytest_asyncio
import uuid

from app.db.base import Base
from app.db.session import test_async_engine, TestAsyncSessionLocal
from app.crud.user import user
from app.schemas.user import UserCreate


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

@pytest_asyncio.fixture(scope="function")
async def db_session():
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
