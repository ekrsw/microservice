from typing import Optional
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class CRUDUser:
    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        password = obj_in.password
        hashed_password = await get_password_hash(password)
        db_obj = User(
            username=obj_in.username,
            hashed_password= hashed_password
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[User]:
        result = await db.execute(select(User).filter(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def update(self, db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        if obj_in.username is not None:
            db_obj.username = obj_in.username
        if obj_in.password is not None:
            db_obj.hashed_password = await get_password_hash(obj_in.password)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, db_obj: User) -> None:
        await db.delete(db_obj)
        await db.commit()

user = CRUDUser()