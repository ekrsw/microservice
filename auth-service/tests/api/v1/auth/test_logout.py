import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.crud.user import user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_logout_success(db_session, test_user, async_client):
    """
    正常系テスト：有効なリフレッシュトークンでログアウトできることを確認
    """
    # まずログインしてリフレッシュトークンを取得
    login_data = {
        "username": test_user.username,
        "password": "test_password123"
    }
    
    login_response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert login_response.status_code == status.HTTP_200_OK
    login_data = login_response.json()
    refresh_token = login_data["refresh_token"]
    
    # リフレッシュトークンを使用してログアウト
    logout_data = {
        "refresh_token": refresh_token
    }
    
    logout_response = await async_client.post(
        "/api/v1/auth/logout",
        json=logout_data
    )
    
    # レスポンスの検証
    assert logout_response.status_code == status.HTTP_200_OK
    logout_result = logout_response.json()
    assert "detail" in logout_result
    assert "ログアウトしました" in logout_result["detail"]
    
    # ログアウト後に同じリフレッシュトークンを使用してリフレッシュを試みる
    # （トークンが無効化されているはず）
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    refresh_response = await async_client.post(
        "/api/v1/auth/refresh",
        json=refresh_data
    )
    
    # リフレッシュトークンが無効化されていることを確認
    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = refresh_response.json()
    assert "detail" in error_data
    assert "リフレッシュトークンが無効です" in error_data["detail"]


@pytest.mark.asyncio
async def test_logout_invalid_token(db_session, async_client):
    """
    異常系テスト：無効なリフレッシュトークンでログアウトするとエラーになることを確認
    """
    # 無効なリフレッシュトークン
    invalid_logout_data = {
        "refresh_token": "invalid_refresh_token"
    }
    
    response = await async_client.post(
        "/api/v1/auth/logout",
        json=invalid_logout_data
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_data = response.json()
    assert "detail" in error_data
    assert "無効なトークンです" in error_data["detail"]
