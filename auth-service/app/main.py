from app.crud.user import user
from app.db.session import AsyncSessionLocal, async_engine
from app.schemas.user import UserCreate
from app.db.base import Base

async def func():
    # データベースのテーブルを作成
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # ユーザー作成
        user_in = UserCreate(
            username="testuser",
            password="testpassword"
        )
        db_user = await user.create(db, obj_in=user_in)
        print(f"Created user: {db_user.username}")

        # ユーザー取得
        found_user = await user.get_by_username(db, username="testuser")
        print(f"Found user: {found_user.username}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(func())