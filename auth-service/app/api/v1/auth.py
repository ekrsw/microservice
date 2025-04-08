import uuid
from typing import Any, List, Optional
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud.user import user
from app.db.session import get_db
from app.schemas.user import UserCreate, UserUpdate, User as UserResponse, Token, RefreshToken
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    verify_refresh_token,
    revoke_refresh_token
)
from app.core.config import settings
from app.api.deps import validate_refresh_token, get_current_user, get_current_admin_user, get_optional_current_user
from app.core.logging import get_request_logger, app_logger
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
    ) -> Any:
    """
    ユーザーを登録するエンドポイント
    - 管理者ユーザーのみがadmin=Trueのユーザーを登録可能
    - 認証されていないユーザーはadmin=Falseのユーザーのみ登録可能
    """
    logger = get_request_logger(request)
    
    # 認証されていないユーザーの場合
    if current_user is None:
        logger.info(f"未認証ユーザーからの登録リクエスト: {user_in.username}")
        
        # 未認証ユーザーがadmin=Trueのユーザーを登録しようとした場合
        if user_in.is_admin:
            logger.warning(f"ユーザー登録失敗: 未認証ユーザーは管理者ユーザーを登録できません")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理者ユーザーを登録する権限がありません"
            )
    else:
        # 認証済みユーザーの場合
        logger.info(f"ユーザー登録リクエスト: {user_in.username}, 要求元={current_user.username}")
        
        # 管理者権限チェック - admin=Trueのユーザーを登録する場合は管理者権限が必要
        if user_in.is_admin and not current_user.is_admin:
            logger.warning(f"ユーザー登録失敗: 権限不足 (ユーザー '{current_user.username}' は管理者ではありません)")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理者ユーザーを登録する権限がありません"
            )
    
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
    
    logger.info(f"ユーザー登録成功: ID={new_user.id}, ユーザー名={new_user.username}, 管理者={new_user.is_admin}")
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


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    全ユーザーを取得するエンドポイント（管理者のみ）
    """
    logger = get_request_logger(request)
    logger.info(f"全ユーザー取得リクエスト: 要求元={current_user.username}")
    
    users = await user.get_all_users(db)
    return users


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    ユーザー情報を更新するエンドポイント
    - 自分自身または管理者のみがユーザー情報を更新可能
    - is_adminフラグは管理者のみが変更可能
    """
    logger = get_request_logger(request)
    logger.info(f"ユーザー更新リクエスト: 対象ID={user_id}, 要求元={current_user.username}")
    
    # 更新対象ユーザーの取得
    db_user = await user.get_by_id(db, id=user_id)
    if not db_user:
        logger.warning(f"ユーザー更新失敗: ユーザーID '{user_id}' が存在しません")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定されたユーザーが見つかりません"
        )
    
    # 権限チェック
    # 1. 自分以外のユーザーを更新する場合は管理者権限が必要
    # 2. is_adminフラグを変更する場合は管理者権限が必要
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
        logger.warning(f"ユーザー更新失敗: 権限不足 (ユーザー '{current_user.username}' は管理者ではありません)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="他のユーザーを更新する権限がありません"
        )
    
    # 一般ユーザーがis_adminフラグを変更しようとした場合
    if user_in.is_admin is not None and user_in.is_admin != db_user.is_admin and not current_user.is_admin:
        logger.warning(f"ユーザー更新失敗: 権限不足 (ユーザー '{current_user.username}' は管理者フラグを変更できません)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限を変更する権限がありません"
        )
    
    # ユーザー更新
    try:
        updated_user = await user.update(db, db_user, user_in)
        logger.info(f"ユーザー更新成功: ID={updated_user.id}, ユーザー名={updated_user.username}")
        return updated_user
    except IntegrityError:
        logger.error(f"ユーザー更新失敗: データベースエラー", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザー名が既に使用されています"
        )
    except Exception as e:
        logger.error(f"ユーザー更新失敗: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー更新中にエラーが発生しました"
        )
