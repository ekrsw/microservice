from typing import Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID


# 共通のプロパティを持つUserBaseクラス
class UserBase(BaseModel):
    username: Optional[str] = None
    is_admin: Optional[bool] = False


# 新規ユーザー作成時に必要なプロパティ
class UserCreate(UserBase):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=16)


# ユーザー更新時に使うプロパティ
class UserUpdate(UserBase):
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=16)
    is_active: Optional[bool] = None


# レスポンスとして返すユーザー情報
class UserInDBBase(UserBase):
    id: UUID
    username: str
    is_admin: bool
    is_active: bool

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


# トークン関連のスキーマ
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class RefreshToken(BaseModel):
    refresh_token: str
