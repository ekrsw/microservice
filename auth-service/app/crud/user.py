from typing import Optional
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate, AdminUserCreate, UserUpdate, PasswordUpdate
from app.core.security import get_password_hash

class CRUDUser:
    async def create(self, db: AsyncSession, obj_in: UserCreate | AdminUserCreate) -> User:
        password = obj_in.password
        hashed_password = get_password_hash(password)
        
        # UserCreateの場合はis_adminがないのでFalseをデフォルト値として使用
        is_admin = getattr(obj_in, 'is_admin', False)
        
        db_obj = User(
            username=obj_in.username,
            hashed_password=hashed_password,
            is_admin=is_admin
        )
        db.add(db_obj)
        # コミットは呼び出し元に任せる
        await db.flush() # flush() でセッションに変更を反映
        await db.refresh(db_obj)
        return db_obj
    
    async def get_all_users(self, db: AsyncSession) -> list[User]:
        result = await db.execute(select(User))
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[User]:
        result = await db.execute(select(User).filter(User.id == id))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def update(self, db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        try:
            if obj_in.username is not None:
                db_obj.username = obj_in.username
            if obj_in.is_active is not None:
                db_obj.is_active = obj_in.is_active
            if obj_in.is_admin is not None:
                db_obj.is_admin = obj_in.is_admin
            # コミットは呼び出し元に任せる
            await db.flush() # flush() でセッションに変更を反映
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            # ロールバックは呼び出し元に任せる
            # await db.rollback() # 削除
            raise
    
    async def update_password(self, db: AsyncSession, db_obj: User, new_password: str) -> User:
        """
        ユーザーのパスワードのみを更新する関数
        
        Args:
            db: データベースセッション
            db_obj: 更新対象のユーザーオブジェクト
            new_password: 新しいパスワード
            
        Returns:
            User: 更新されたユーザーオブジェクト
        """
        # try/except は不要になるか、より具体的な例外を捕捉するように変更可能
        # ここではシンプルに削除
        db_obj.hashed_password = get_password_hash(new_password)
        # コミットは呼び出し元に任せる
        # flush() でセッションに変更を反映させる（コミット前）
        await db.flush() 
        await db.refresh(db_obj)
        return db_obj
        # ロールバックも呼び出し元に任せる

    async def delete(self, db: AsyncSession, db_obj: User) -> None:
        # Check if the user exists in the database
        existing_user = await self.get_by_id(db, db_obj.id)
        if not existing_user:
            raise ValueError("User not found")
        
        await db.delete(existing_user)
        # コミットは呼び出し元に任せる
        await db.flush() # flush() でセッションに変更を反映

user = CRUDUser()
