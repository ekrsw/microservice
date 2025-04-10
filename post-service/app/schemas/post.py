from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime

# 基本となるPostスキーマ
class PostBase(BaseModel):
    title: str
    content: Optional[str] = None
    is_published: bool = False

# 投稿作成時のリクエストスキーマ
class PostCreate(PostBase):
    pass

# 投稿更新時のリクエストスキーマ
class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None

# データベース内の完全なPostモデル
class PostInDB(PostBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# APIレスポンス用スキーマ
class Post(PostInDB):
    pass
