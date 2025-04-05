from app.crud.user import user
from app.db.session import AsyncSessionLocal
import asyncio


async def func():
    async with AsyncSessionLocal() as db:
        all_users = await user.get_all_users(db)
    
    print(type(all_users))
    for u in all_users:
        print(u.username)

if __name__ == "__main__":
    asyncio.run(func())