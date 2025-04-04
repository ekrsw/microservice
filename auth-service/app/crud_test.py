from app.crud.user import user
from app.db.session import async_engine
from app.schemas.user import UserCreate
from app.db.base import Base
from app.db.session import get_db

async def func():
    # データベースのテーブルを作成
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for db in get_db():
        # ユーザー作成
        user_in = UserCreate(
            username="testuser2",
            password="testpassword"
        )
        db_user = await user.create(db, obj_in=user_in)
        print(f"Created user: {db_user.username}")

        # ユーザー取得
        found_user = await user.get_by_username(db, username="testuser2")
        print(f"Found user: {found_user.username}")
        print(f"User ID: {found_user.id}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(func())