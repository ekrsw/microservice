import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_get_user_me_success(db_session, test_user, async_client):
    """
    正常系テスト：認証されたユーザーが自分自身の情報を取得できることを確認
    """
    # アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # APIリクエスト
    response = await async_client.get(
        "/api/v1/auth/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["id"] == str(test_user.id)
    assert user_data["username"] == test_user.username
    assert user_data["is_admin"] == test_user.is_admin
    assert user_data["is_active"] == test_user.is_active

@pytest.mark.asyncio
async def test_get_user_me_admin_success(db_session, admin_user, async_client):
    """
    正常系テスト：管理者ユーザーが自分自身の情報を取得できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # APIリクエスト
    response = await async_client.get(
        "/api/v1/auth/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["id"] == str(admin_user.id)
    assert user_data["username"] == admin_user.username
    assert user_data["is_admin"] == True  # 管理者であることを確認
    assert user_data["is_active"] == admin_user.is_active

@pytest.mark.asyncio
async def test_get_user_me_unauthorized(db_session, async_client):
    """
    異常系テスト：認証なしでアクセスすると401エラーになることを確認
    """
    # 認証なしでAPIリクエスト
    response = await async_client.get("/api/v1/auth/user/me")
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data

@pytest.mark.asyncio
async def test_get_user_me_invalid_token(db_session, async_client):
    """
    異常系テスト：無効なトークンでアクセスすると401エラーになることを確認
    """
    # 無効なトークンでAPIリクエスト
    response = await async_client.get(
        "/api/v1/auth/user/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data
