from fastapi import APIRouter
from app.api.v1 import post, auth

api_router = APIRouter()

# 認証関連のルーターを登録
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 投稿関連のルーターを登録
api_router.include_router(post.router, prefix="/posts", tags=["posts"])
