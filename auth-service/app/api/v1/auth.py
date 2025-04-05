import uuid
from typing import Any
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
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
from app.core.logging import get_request_logger, app_logger

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
    ) -> Any:
    """
    ユーザーを登録するエンドポイント
    """
    logger = get_request_logger(request)
    logger.info(f"ユーザー登録リクエスト: {user_in.username}")
    
    # ユーザー名の重複チェック
    existing_user = await user.get_by_username(db, username=user_in.username)
    if existing_user:
        logger.warning(f"ユーザー登録失敗: ユーザー名 '{user_in.username}' は既に使用されています")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このユーザー名は既に登録されています。"
        )
    
    # ユーザー作成
    new_user = await user.create(db, user_in)
    if not new_user:
        logger.error(f"ユーザー登録失敗: '{user_in.username}' の作成中にエラーが発生しました")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザーの登録に失敗しました。"
        )
    
    logger.info(f"ユーザー登録成功: ID={new_user.id}, ユーザー名={new_user.username}")
    return new_user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    ユーザーログインとトークン発行のエンドポイント
    """
    logger = get_request_logger(request)
    logger.info(f"ログインリクエスト: ユーザー名={form_data.username}")
    
    # ユーザー認証
    db_user = await user.get_by_username(db, username=form_data.username)
    if not db_user:
        logger.warning(f"ログイン失敗: ユーザー名 '{form_data.username}' が存在しません")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # パスワード検証
    if not await verify_password(form_data.password, db_user.hashed_password):
        logger.warning(f"ログイン失敗: ユーザー '{form_data.username}' のパスワードが不正です")
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
    
    logger.info(f"ログイン成功: ユーザーID={db_user.id}, ユーザー名={db_user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    リフレッシュトークンを使用して新しいアクセストークンを発行するエンドポイント
    """
    logger = get_request_logger(request)
    logger.info("トークン更新リクエスト")
    
    try:
        # リフレッシュトークンの検証
        user_id = await validate_refresh_token(token_data.refresh_token)
        
        # ユーザーの存在確認
        db_user = await user.get_by_id(db, id=UUID(user_id))
        if not db_user:
            logger.warning(f"トークン更新失敗: ユーザーID '{user_id}' が存在しません")
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
        
        logger.info(f"トークン更新成功: ユーザーID={db_user.id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"トークン更新中にエラーが発生しました: {str(e)}", exc_info=True)
        raise


@router.post("/logout")
async def logout(
    request: Request,
    token_data: RefreshToken
) -> Any:
    """
    ログアウトしてリフレッシュトークンを無効化するエンドポイント
    """
    logger = get_request_logger(request)
    logger.info("ログアウトリクエスト")
    
    try:
        # リフレッシュトークンを無効化
        result = await revoke_refresh_token(token_data.refresh_token)
        
        if not result:
            logger.warning("ログアウト失敗: 無効なトークン")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無効なトークンです",
            )
        
        logger.info("ログアウト成功: トークンを無効化しました")
        return {"detail": "ログアウトしました"}
    except Exception as e:
        logger.error(f"ログアウト処理中にエラーが発生しました: {str(e)}", exc_info=True)
        raise
