from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, EmailStr


# 共通のプロパティを持つUserBaseクラス
class UserBase(BaseModel):
    username: Optional[str] = None

# 新規ユーザー作成時に必要なプロパティ
class UserCreate(UserBase):
    username: str
    password: str


# ユーザー更新時に使うプロパティ
class UserUpdate(UserBase):
    password: Optional[str] = None


# レスポンスとして返すユーザー情報
class UserInDBBase(UserBase):
    id: Optional[UUID] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


# APIレスポンスで使用するユーザースキーマ
class User(UserInDBBase):
    pass


# データベース内部で使用するスキーマ（パスワードハッシュを含む）
class UserInDB(UserInDBBase):
    hashed_password: str