# 正常系テスト
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from jose import jwt, JWTError
import fakeredis.aioredis
from unittest.mock import patch, AsyncMock
from freezegun import freeze_time

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token
)
from app.core.config import settings


# パスワード関連のテスト
@pytest.mark.asyncio
async def test_get_password_hash_success():
    """パスワードのハッシュ化が正しく行われるかテスト"""
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    
    # ハッシュ化されたパスワードが元のパスワードと異なることを確認
    assert hashed_password != password
    # ハッシュ化されたパスワードが適切な形式であることを確認
    assert hashed_password.startswith("$2b$")  # bcryptのプレフィックス


@pytest.mark.asyncio
async def test_verify_password_success():
    """正しいパスワードが検証できるかテスト"""
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    
    # 正しいパスワードで検証
    is_valid = verify_password(password, hashed_password)
    assert is_valid is True
    
    # 誤ったパスワードで検証
    is_valid = verify_password("wrongpassword", hashed_password)
    assert is_valid is False


# アクセストークン関連のテスト
@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_create_access_token_success():
    """基本的なアクセストークン生成のテスト"""
    # テスト用のデータ
    data = {"sub": "testuser"}
    
    # トークン生成
    token = await create_access_token(data)
    
    # トークンをデコードして検証
    payload = jwt.decode(
        token, 
        settings.PUBLIC_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    
    # ペイロードに正しいデータが含まれていることを確認
    assert payload["sub"] == "testuser"
    
    # デフォルトの有効期限が設定されていることを確認
    expected_exp = datetime(2025, 1, 1, 12, 0, 0) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    assert datetime.fromtimestamp(payload["exp"]) == expected_exp


@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_create_access_token_with_custom_exp():
    """カスタム有効期限を指定したアクセストークン生成のテスト"""
    # テスト用のデータ
    data = {"sub": "testuser"}
    custom_expires = timedelta(hours=2)
    
    # カスタム有効期限でトークン生成
    token = await create_access_token(data, expires_delta=custom_expires)
    
    # トークンをデコードして検証
    payload = jwt.decode(
        token, 
        settings.PUBLIC_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    
    # ペイロードに正しいデータが含まれていることを確認
    assert payload["sub"] == "testuser"
    
    # カスタム有効期限が設定されていることを確認
    expected_exp = datetime(2025, 1, 1, 12, 0, 0) + custom_expires
    assert datetime.fromtimestamp(payload["exp"]) == expected_exp


# リフレッシュトークン関連のテスト
@pytest_asyncio.fixture
async def mock_redis():
    """Redisのモックを提供するフィクスチャ"""
    with patch('redis.asyncio.from_url') as mock_redis:
        # fakeredisを使用してRedisをモック
        fake_redis = fakeredis.aioredis.FakeRedis()
        mock_redis.return_value = fake_redis
        yield fake_redis


@pytest.mark.asyncio
async def test_create_refresh_token_success(mock_redis):
    """リフレッシュトークン生成のテスト"""
    user_id = "test-user-id"
    
    # リフレッシュトークン生成
    token = await create_refresh_token(user_id)
    
    # トークンが生成されていることを確認
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Redisに保存されていることを確認
    stored_user_id = await mock_redis.get(f"refresh_token:{token}")
    assert stored_user_id is not None
    assert stored_user_id.decode("utf-8") == user_id
    
    # 有効期限が設定されていることを確認
    ttl = await mock_redis.ttl(f"refresh_token:{token}")
    expected_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    # TTLは厳密に一致しないことがあるため、近似値で確認
    assert ttl > 0
    assert abs(ttl - expected_ttl) < 10  # 10秒以内の誤差を許容


@pytest.mark.asyncio
async def test_verify_refresh_token_success(mock_redis):
    """リフレッシュトークン検証のテスト"""
    user_id = "test-user-id"
    token = "test-refresh-token"
    
    # Redisにテスト用のトークンを保存
    await mock_redis.setex(
        f"refresh_token:{token}", 
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        user_id
    )
    
    # トークン検証
    result = await verify_refresh_token(token)
    
    # 正しいユーザーIDが返されることを確認
    assert result == user_id


@pytest.mark.asyncio
async def test_revoke_refresh_token_success(mock_redis):
    """リフレッシュトークン無効化のテスト"""
    user_id = "test-user-id"
    token = "test-refresh-token"
    
    # Redisにテスト用のトークンを保存
    await mock_redis.setex(
        f"refresh_token:{token}", 
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        user_id
    )
    
    # トークンが保存されていることを確認
    stored_user_id = await mock_redis.get(f"refresh_token:{token}")
    assert stored_user_id is not None
    
    # トークン無効化
    result = await revoke_refresh_token(token)
    
    # 無効化が成功したことを確認
    assert result is True
    
    # トークンがRedisから削除されていることを確認
    stored_user_id = await mock_redis.get(f"refresh_token:{token}")
    assert stored_user_id is None
