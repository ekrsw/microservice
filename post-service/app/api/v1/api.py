from fastapi import APIRouter
from app.api.v1 import post

api_router = APIRouter()

# 投稿関連のルーターを登録
api_router.include_router(post.router, prefix="/posts", tags=["posts"])
