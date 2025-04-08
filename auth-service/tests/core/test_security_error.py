# エラー系テスト
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from jose import jwt, JWTError
import fakeredis.aioredis
from unittest.mock import patch, AsyncMock, MagicMock
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


# パスワード関連のエラーテスト
@pytest.mark.asyncio
async def test_verify_password_with_wrong_password():
    """誤ったパスワードでの検証テスト"""
    correct_password = "correctpassword123"
    wrong_password = "wrongpassword123"
    
    # 正しいパスワードでハッシュを生成
    hashed_password = await get_password_hash(correct_password)
    
    # 誤ったパスワードで検証
    is_valid = await verify_password(wrong_password, hashed_password)
    
    # 検証が失敗することを確認
    assert is_valid is False


@pytest.mark.asyncio
async def test_verify_password_with_invalid_hash():
    """無効なハッシュでの検証テスト"""
    password = "testpassword123"
    invalid_hash = "invalid_hash_format"
    
    # 無効なハッシュで検証
    with pytest.raises(ValueError) as exc_info:
        await verify_password(password, invalid_hash)
    
    # エラーメッセージを確認
    assert "hash could not be identified" in str(exc_info.value).lower()


# アクセストークン関連のエラーテスト
@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_decode_token_with_wrong_secret():
    """誤った秘密鍵でのトークンデコードテスト"""
    data = {"sub": "testuser"}
    
    # 正しい秘密鍵でトークン生成
    token = await create_access_token(data)
    
    # 誤った公開鍵でデコード
    wrong_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu1SU1LfVLPHCozMxH2Mo
4lgOEePzNm0tRgeLezV6ffAt0gunVTLw7onLRnrq0/IzW7yWR7QkrmBL7jTKEn5u
+qKhbwKfBstIs+bMY2Zkp18gnTxKLxoS2tFczGkPLPgizskuemMghRniWaoLcyeh
kd3qqGElvW/VDL5AaWTg0nLVkjRo9z+40RQzuVaE8AkAFmxZzow3x+VJYKdjykkJ
0iT9wCS0DRTXu269V264Vf/3jvredZiKRkgwlL9xNAwxXFg0x/XFw005UWVRIkdg
cKWTjpBP2dPwVZ4WWC+9aGVd+Gyn1o0CLelf4rEjGoXbAAEgAqeGUxrcIlbjXfbc
mwIDAQAB
-----END PUBLIC KEY-----"""
    with pytest.raises(JWTError):
        jwt.decode(token, wrong_key, algorithms=[settings.ALGORITHM])


@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_decode_token_with_wrong_algorithm():
    """誤ったアルゴリズムでのトークンデコードテスト"""
    data = {"sub": "testuser"}
    
    # 正しいアルゴリズムでトークン生成
    token = await create_access_token(data)
    
    # 誤ったアルゴリズムでデコード
    wrong_algorithm = "RS512"  # 正しくはRS256
    with pytest.raises(JWTError):
        jwt.decode(token, settings.PUBLIC_KEY, algorithms=[wrong_algorithm])


@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_decode_expired_token():
    """期限切れトークンのデコードテスト"""
    data = {"sub": "testuser"}
    
    # 短い有効期限でトークン生成
    token = await create_access_token(data, expires_delta=timedelta(seconds=1))
    
    # 時間を進めて期限切れにする
    with freeze_time("2025-01-01 12:00:02"):  # 2秒後
        # 期限切れトークンをデコード
        with pytest.raises(JWTError) as exc_info:
            jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
        
        # エラーメッセージを確認
        assert "expired" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_decode_invalid_token_format():
    """無効な形式のトークンデコードテスト"""
    invalid_token = "invalid.token.format"
    
    # 無効なトークンをデコード
    with pytest.raises(JWTError):
        jwt.decode(invalid_token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])


# リフレッシュトークン関連のエラーテスト
@pytest_asyncio.fixture
async def mock_redis():
    """Redisのモックを提供するフィクスチャ"""
    with patch('redis.asyncio.from_url') as mock_redis:
        # fakeredisを使用してRedisをモック
        fake_redis = fakeredis.aioredis.FakeRedis()
        mock_redis.return_value = fake_redis
        yield fake_redis


@pytest.mark.asyncio
async def test_verify_refresh_token_invalid(mock_redis):
    """無効なリフレッシュトークンの検証テスト"""
    # 存在しないトークン
    non_existent_token = "non-existent-token"
    
    # トークン検証
    result = await verify_refresh_token(non_existent_token)
    
    # 結果がNoneであることを確認
    assert result is None


@pytest.mark.asyncio
async def test_verify_refresh_token_expired(mock_redis):
    """期限切れリフレッシュトークンの検証テスト"""
    import asyncio
    
    user_id = "test-user-id"
    token = "test-refresh-token"
    
    # トークンを保存（有効期限を1秒に設定）
    await mock_redis.setex(f"refresh_token:{token}", 1, user_id)
    
    # 有効期限が切れるまで待機
    await asyncio.sleep(1.5)
    
    # トークン検証
    result = await verify_refresh_token(token)
    
    # 結果がNoneであることを確認
    assert result is None


@pytest.mark.asyncio
async def test_revoke_refresh_token_not_found(mock_redis):
    """存在しないリフレッシュトークンの無効化テスト"""
    # 存在しないトークン
    non_existent_token = "non-existent-token"
    
    # トークン無効化
    result = await revoke_refresh_token(non_existent_token)
    
    # 結果がFalseであることを確認
    assert result is False


@pytest.mark.asyncio
async def test_redis_connection_error():
    """Redis接続エラーのテスト"""
    # Redisクライアントをモックしてエラーを発生させる
    with patch('redis.asyncio.from_url') as mock_redis:
        # 例外を発生させるモック
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Redis connection error")
        mock_client.delete.side_effect = Exception("Redis connection error")
        mock_client.setex.side_effect = Exception("Redis connection error")
        mock_client.close = AsyncMock()
        mock_redis.return_value = mock_client
        
        # リフレッシュトークン検証
        with pytest.raises(Exception) as exc_info:
            await verify_refresh_token("test-token")
        
        # エラーメッセージを確認
        assert "redis connection error" in str(exc_info.value).lower()
        
        # リフレッシュトークン無効化
        with pytest.raises(Exception) as exc_info:
            await revoke_refresh_token("test-token")
        
        # エラーメッセージを確認
        assert "redis connection error" in str(exc_info.value).lower()
        
        # リフレッシュトークン生成
        with pytest.raises(Exception) as exc_info:
            await create_refresh_token("test-user-id")
        
        # エラーメッセージを確認
        assert "redis connection error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_access_token_with_invalid_data():
    """無効なデータでのアクセストークン生成テスト"""
    # 無効なデータ（シリアライズできない）
    invalid_data = {"user": object()}  # objectはJSONシリアライズできない
    
    # トークン生成
    with pytest.raises(TypeError) as exc_info:
        await create_access_token(invalid_data)
    
    # エラーメッセージを確認
    assert "not json serializable" in str(exc_info.value).lower()
