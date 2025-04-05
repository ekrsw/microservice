import uuid
from typing import Any
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import user
from app.db.session import get_db
from app.schemas.user import UserCreate, User as UserResponse, Token, RefreshToken
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    verify_refresh_token,
    revoke_refresh_token
)
from app.core.config import settings
from app.api.deps import validate_refresh_token

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


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    ユーザーログインとトークン発行のエンドポイント
    """
    # ユーザー認証
    db_user = await user.get_by_username(db, username=form_data.username)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # パスワード検証
    if not await verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アクセストークン生成
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": str(db_user.id)},
        expires_delta=access_token_expires
    )
    
    # リフレッシュトークン生成
    refresh_token = await create_refresh_token(user_id=str(db_user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    リフレッシュトークンを使用して新しいアクセストークンを発行するエンドポイント
    """
    # リフレッシュトークンの検証
    user_id = await validate_refresh_token(token_data.refresh_token)
    
    # ユーザーの存在確認
    db_user = await user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なユーザーです",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 古いリフレッシュトークンを無効化
    await revoke_refresh_token(token_data.refresh_token)
    
    # 新しいアクセストークンの生成
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": str(db_user.id)},
        expires_delta=access_token_expires
    )
    
    # 新しいリフレッシュトークンの生成
    refresh_token = await create_refresh_token(user_id=str(db_user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(token_data: RefreshToken) -> Any:
    """
    ログアウトしてリフレッシュトークンを無効化するエンドポイント
    """
    # リフレッシュトークンを無効化
    result = await revoke_refresh_token(token_data.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無効なトークンです",
        )
    
    return {"detail": "ログアウトしました"}
