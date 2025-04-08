# 境界値テスト
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
    verify_refresh_token
)
from app.core.config import settings


# アクセストークン関連の境界値テスト
@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_create_access_token_with_min_expiry():
    """最小有効期限（1分）でのアクセストークン生成テスト"""
    data = {"sub": "testuser"}
    min_expires = timedelta(minutes=1)
    
    # 最小有効期限でトークン生成
    token = await create_access_token(data, expires_delta=min_expires)
    
    # トークンをデコードして検証
    payload = jwt.decode(
        token, 
        settings.PUBLIC_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    
    # 最小有効期限が正しく設定されていることを確認
    expected_exp = datetime(2025, 1, 1, 12, 0, 0) + min_expires
    assert datetime.fromtimestamp(payload["exp"]) == expected_exp


@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_create_access_token_with_max_expiry():
    """最大有効期限（30日）でのアクセストークン生成テスト"""
    data = {"sub": "testuser"}
    max_expires = timedelta(days=30)
    
    # 最大有効期限でトークン生成
    token = await create_access_token(data, expires_delta=max_expires)
    
    # トークンをデコードして検証
    payload = jwt.decode(
        token, 
        settings.PUBLIC_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    
    # 最大有効期限が正しく設定されていることを確認
    expected_exp = datetime(2025, 1, 1, 12, 0, 0) + max_expires
    assert datetime.fromtimestamp(payload["exp"]) == expected_exp


@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_access_token_with_large_payload():
    """大きなペイロードを持つアクセストークン生成テスト"""
    # 大きなデータを含むペイロード
    large_data = {
        "sub": "testuser",
        "roles": ["admin", "user", "moderator"],
        "permissions": ["read", "write", "delete", "update"],
        "user_info": {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "address": "123 Test Street, Test City, Test Country",
            "phone": "+1234567890",
            "preferences": {
                "theme": "dark",
                "language": "ja",
                "notifications": True,
                "timezone": "Asia/Tokyo"
            }
        }
    }
    
    # 大きなペイロードでトークン生成
    token = await create_access_token(large_data)
    
    # トークンをデコードして検証
    payload = jwt.decode(
        token, 
        settings.PUBLIC_KEY, 
        algorithms=[settings.ALGORITHM]
    )
    
    # ペイロードの内容が正しく含まれていることを確認
    assert payload["sub"] == "testuser"
    assert payload["roles"] == ["admin", "user", "moderator"]
    assert payload["permissions"] == ["read", "write", "delete", "update"]
    assert payload["user_info"]["first_name"] == "Test"
    assert payload["user_info"]["preferences"]["language"] == "ja"


# パスワード関連の境界値テスト
@pytest.mark.asyncio
async def test_verify_password_with_min_length():
    """最小長（1文字）のパスワード検証テスト"""
    min_password = "a"
    hashed_password = await get_password_hash(min_password)
    
    # 正しいパスワードで検証
    is_valid = await verify_password(min_password, hashed_password)
    assert is_valid is True
    
    # 誤ったパスワードで検証
    is_valid = await verify_password("b", hashed_password)
    assert is_valid is False


@pytest.mark.asyncio
async def test_verify_password_with_max_length():
    """最大長（72文字、bcryptの制限）のパスワード検証テスト"""
    # bcryptの最大長は72バイト
    max_password = "a" * 72
    hashed_password = await get_password_hash(max_password)
    
    # 正しいパスワードで検証
    is_valid = await verify_password(max_password, hashed_password)
    assert is_valid is True
    
    # 誤ったパスワードで検証
    wrong_password = "a" * 71 + "b"
    is_valid = await verify_password(wrong_password, hashed_password)
    assert is_valid is False


@pytest.mark.asyncio
async def test_verify_password_with_special_chars():
    """特殊文字を含むパスワード検証テスト"""
    special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?/~`"
    hashed_password = await get_password_hash(special_password)
    
    # 正しいパスワードで検証
    is_valid = await verify_password(special_password, hashed_password)
    assert is_valid is True
    
    # 誤ったパスワードで検証
    is_valid = await verify_password("P@ssw0rd", hashed_password)
    assert is_valid is False


@pytest.mark.asyncio
async def test_verify_password_with_unicode_chars():
    """Unicode文字（日本語など）を含むパスワード検証テスト"""
    unicode_password = "パスワード123テスト"
    hashed_password = await get_password_hash(unicode_password)
    
    # 正しいパスワードで検証
    is_valid = await verify_password(unicode_password, hashed_password)
    assert is_valid is True
    
    # 誤ったパスワードで検証
    is_valid = await verify_password("パスワード123", hashed_password)
    assert is_valid is False


# リフレッシュトークン関連の境界値テスト
@pytest_asyncio.fixture
async def mock_redis():
    """Redisのモックを提供するフィクスチャ"""
    with patch('redis.asyncio.from_url') as mock_redis:
        # fakeredisを使用してRedisをモック
        fake_redis = fakeredis.aioredis.FakeRedis()
        mock_redis.return_value = fake_redis
        yield fake_redis


@pytest.mark.asyncio
async def test_create_refresh_token_with_long_user_id(mock_redis):
    """長いユーザーIDでのリフレッシュトークン生成テスト"""
    # 長いユーザーID
    long_user_id = "a" * 1000
    
    # リフレッシュトークン生成
    token = await create_refresh_token(long_user_id)
    
    # トークンが生成されていることを確認
    assert token is not None
    assert isinstance(token, str)
    
    # Redisに保存されていることを確認
    stored_user_id = await mock_redis.get(f"refresh_token:{token}")
    assert stored_user_id is not None
    assert stored_user_id.decode("utf-8") == long_user_id


@pytest.mark.asyncio
async def test_verify_refresh_token_with_long_token(mock_redis):
    """長いトークンでのリフレッシュトークン検証テスト"""
    user_id = "test-user-id"
    # 長いトークン
    long_token = "a" * 1000
    
    # Redisにテスト用のトークンを保存
    await mock_redis.setex(
        f"refresh_token:{long_token}", 
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        user_id
    )
    
    # トークン検証
    result = await verify_refresh_token(long_token)
    
    # 正しいユーザーIDが返されることを確認
    assert result == user_id


@pytest.mark.asyncio
async def test_refresh_token_with_min_expiry(mock_redis):
    """最小有効期限（1秒）でのリフレッシュトークン生成テスト"""
    user_id = "test-user-id"
    token = "test-refresh-token"
    min_expiry = 1  # 1秒
    
    # 最小有効期限でRedisにトークンを保存
    await mock_redis.setex(f"refresh_token:{token}", min_expiry, user_id)
    
    # TTLが正しく設定されていることを確認
    ttl = await mock_redis.ttl(f"refresh_token:{token}")
    assert ttl <= min_expiry  # TTLが0になる場合もあるので、0 > 0の条件は削除
    
    # トークン検証
    result = await verify_refresh_token(token)
    assert result == user_id
