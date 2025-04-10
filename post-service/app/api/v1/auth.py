from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any, Dict

from app.schemas.auth import Token, RefreshToken
from app.core.auth_client import auth_client
from app.core.logging import get_request_logger

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    ユーザーログインとトークン発行のエンドポイント
    
    auth-serviceのログインエンドポイントを呼び出し、トークンを取得します。
    """
    logger = get_request_logger(request)
    logger.info(f"ログインリクエスト: ユーザー名={form_data.username}")
    
    try:
        # auth-serviceのログインエンドポイントを呼び出す
        token_data = await auth_client.login(form_data.username, form_data.password)
        logger.info(f"ログイン成功: ユーザー名={form_data.username}")
        return token_data
    except HTTPException as e:
        logger.warning(f"ログイン失敗: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"ログイン処理中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン処理中にエラーが発生しました"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_data: RefreshToken
) -> Any:
    """
    リフレッシュトークンを使用して新しいアクセストークンを発行するエンドポイント
    
    auth-serviceのリフレッシュエンドポイントを呼び出し、新しいトークンを取得します。
    """
    logger = get_request_logger(request)
    logger.info("トークン更新リクエスト")
    
    try:
        # auth-serviceのリフレッシュエンドポイントを呼び出す
        new_token_data = await auth_client.refresh_token(token_data.refresh_token)
        logger.info("トークン更新成功")
        return new_token_data
    except HTTPException as e:
        logger.warning(f"トークン更新失敗: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"トークン更新処理中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="トークン更新処理中にエラーが発生しました"
        )

@router.post("/logout")
async def logout(
    request: Request,
    token_data: RefreshToken
) -> Any:
    """
    ログアウトしてリフレッシュトークンを無効化するエンドポイント
    
    auth-serviceのログアウトエンドポイントを呼び出し、トークンを無効化します。
    """
    logger = get_request_logger(request)
    logger.info("ログアウトリクエスト")
    
    try:
        # auth-serviceのログアウトエンドポイントを呼び出す
        result = await auth_client.logout(token_data.refresh_token)
        logger.info("ログアウト成功")
        return result
    except HTTPException as e:
        logger.warning(f"ログアウト失敗: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"ログアウト処理中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログアウト処理中にエラーが発生しました"
        )
