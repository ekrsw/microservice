from passlib.context import CryptContext
from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
import secrets
import redis.asyncio as redis
from typing import Optional, Dict, Any
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    非対称暗号を使用してアクセストークンを作成する関数
    
    Args:
        data: トークンに含めるデータ（通常はユーザーID）
        expires_delta: トークンの有効期限（指定がない場合はデフォルト値を使用）
        
    Returns:
        str: 生成されたJWTトークン
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # 秘密鍵を使用してトークンを署名
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.PRIVATE_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

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
        return payload
    except JWTError:
        return None

async def verify_token_with_fallback(token: str) -> Optional[Dict[str, Any]]:
    """
    両方の方式をサポートする移行期間用のトークン検証関数
    
    Args:
        token: 検証するJWTトークン
        
    Returns:
        Optional[Dict[str, Any]]: トークンが有効な場合はペイロード、無効な場合はNone
    """
    # まず新しい非対称鍵で検証を試みる
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=["RS256"])
        return payload
    except JWTError:
        # 失敗したら古い対称鍵で検証を試みる
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return payload
        except JWTError:
            return None

async def create_refresh_token(user_id: str) -> str:
    """
    リフレッシュトークンを作成し、Redisに保存する関数
    
    Args:
        user_id: ユーザーID
        
    Returns:
        str: 生成されたリフレッシュトークン
    """
    # ランダムなトークンを生成
    token = secrets.token_urlsafe(32)
    
    # Redisクライアントを初期化
    r = redis.from_url(settings.REDIS_URL)
    
    # トークンをRedisに保存（キー: トークン, 値: ユーザーID）
    # 有効期限を設定
    expiry = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 日数を秒に変換
    await r.setex(f"refresh_token:{token}", expiry, user_id)
    
    # 接続を閉じる
    await r.aclose()
    
    return token

async def verify_refresh_token(token: str) -> Optional[str]:
    """
    リフレッシュトークンを検証し、関連するユーザーIDを返す関数
    
    Args:
        token: 検証するリフレッシュトークン
        
    Returns:
        Optional[str]: トークンが有効な場合はユーザーID、無効な場合はNone
    """
    # Redisクライアントを初期化
    r = redis.from_url(settings.REDIS_URL)
    
    # トークンをRedisから取得
    user_id = await r.get(f"refresh_token:{token}")
    
    # 接続を閉じる
    await r.aclose()
    
    if user_id:
        return user_id.decode("utf-8")
    
    return None

async def revoke_refresh_token(token: str) -> bool:
    """
    リフレッシュトークンを無効化する関数
    
    Args:
        token: 無効化するリフレッシュトークン
        
    Returns:
        bool: 無効化に成功した場合はTrue、失敗した場合はFalse
    """
    # Redisクライアントを初期化
    r = redis.from_url(settings.REDIS_URL)
    
    # トークンをRedisから削除
    result = await r.delete(f"refresh_token:{token}")
    
    # 接続を閉じる
    await r.aclose()
    
    return result > 0
