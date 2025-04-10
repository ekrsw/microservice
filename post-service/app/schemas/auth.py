from pydantic import BaseModel, Field
from typing import Optional

class LoginRequest(BaseModel):
    """
    ログインリクエストのスキーマ
    """
    username: str = Field(..., description="ユーザー名")
    password: str = Field(..., description="パスワード")

class Token(BaseModel):
    """
    トークンレスポンスのスキーマ
    """
    access_token: str
    refresh_token: str
    token_type: str

class RefreshToken(BaseModel):
    """
    リフレッシュトークンリクエストのスキーマ
    """
    refresh_token: str
