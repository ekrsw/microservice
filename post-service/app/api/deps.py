from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional, Dict, Any
from uuid import UUID

from app.core.config import settings
from app.db.session import get_db
from app.crud.post import post
from app.models.post import Post
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import app_logger as logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWTトークンを検証し、ペイロードを返す関数
    
    Args:
        token: 検証するJWTトークン
        
    Returns:
        Optional[Dict[str, Any]]: トークンが有効な場合はペイロード、無効な場合はNone
    """
    try:
        # 公開鍵を使用してトークンを検証
        payload = jwt.decode(
            token, 
            settings.PUBLIC_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        logger.debug(f"トークン検証成功: {payload}")
        return payload
    except JWTError as e:
        logger.error(f"トークン検証失敗: {e}")
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    アクセストークンからユーザー情報を取得する依存関数
    
    Args:
        token: JWTアクセストークン
        
    Returns:
        Dict[str, Any]: ユーザー情報を含むペイロード
        
    Raises:
        HTTPException: トークンが無効な場合
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = await verify_token(token)
    if payload is None:
        raise credentials_exception
            
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise credentials_exception
            
    return {"user_id": UUID(user_id), "payload": payload}

async def get_user_post(
    post_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Post:
    """
    投稿を取得し、所有権を確認する依存関数
    
    Args:
        post_id: 投稿ID
        current_user: 現在のユーザー情報
        db: データベースセッション
        
    Returns:
        Post: 投稿オブジェクト
        
    Raises:
        HTTPException: 投稿が存在しない場合、または所有者でない場合
    """
    db_post = await post.get(db, id=post_id)
    if db_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投稿が見つかりません"
        )
    
    if db_post.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作を行う権限がありません"
        )
    
    return db_post
