import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.crud.user import user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_register_user_success(db_session, unique_username, async_client):
    """
    正常系テスト：新規ユーザーが正常に登録できることを確認
    """
    # テストデータ
    test_user = {
        "username": unique_username,
        "password": "test_password123"
    }
    
    # APIリクエスト
    response = await async_client.post("/api/v1/auth/register", json=test_user)
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == unique_username
    assert "id" in data
    
    # IDがUUIDフォーマットであることを確認
    try:
        uuid.UUID(data["id"])
    except ValueError:
        assert False, "IDはUUID形式ではありません"


@pytest.mark.asyncio
async def test_register_user_duplicate_username(db_session, async_client, unique_username):
    """
    異常系テスト：既存のユーザー名で登録しようとするとエラーになることを確認
    """
    # テストデータ
    test_user = {
        "username": unique_username,
        "password": "test_password123"
    }
    
    # 1回目のリクエスト（成功するはず）
    response1 = await async_client.post("/api/v1/auth/register", json=test_user)
    
    # 1回目のレスポンスの検証
    assert response1.status_code == status.HTTP_200_OK
    
    # 2回目の同じユーザー名でのリクエスト（失敗するはず）
    response2 = await async_client.post("/api/v1/auth/register", json=test_user)
    
    # 2回目のレスポンスの検証
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    error_data = response2.json()
    assert "detail" in error_data
    assert "このユーザー名は既に登録されています" in error_data["detail"]
