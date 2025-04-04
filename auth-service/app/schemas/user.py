from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator


# 共通のプロパティを持つUserBaseクラス
class UserBase(BaseModel):
    username: Optional[str] = None


# 新規ユーザー作成時に必要なプロパティ
class UserCreate(UserBase):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=16)


# ユーザー更新時に使うプロパティ
class UserUpdate(UserBase):
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=16)


# レスポンスとして返すユーザー情報
class UserInDBBase(UserBase):
    id: UUID
    username: str

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }


# APIレスポンスで使用するユーザースキーマ
class User(UserInDBBase):
    pass


# データベース内部で使用するスキーマ（パスワードハッシュを含む）
class UserInDB(UserInDBBase):
    hashed_password: str