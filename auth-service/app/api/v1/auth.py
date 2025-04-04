import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import user
from app.db.session import get_db
from app.schemas.user import UserCreate, User as UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
    ) -> Any:
    """
    ユーザーを登録するエンドポイント
    """
    # ユーザー名の重複チェック
    existing_user = await user.get_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に登録されています。"
        )
    
    # ユーザー作成
    new_user = await user.create(db, user_in)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザーの登録に失敗しました。"
        )
    return new_user
