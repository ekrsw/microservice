import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.crud.user import user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_login_success(db_session, test_user, async_client):
    """
    正常系テスト：正しいユーザー名とパスワードでログインできることを確認
    """
    # テストデータ
    login_data = {
        "username": test_user.username,
        "password": "test_password123"  # conftest.pyのtest_userフィクスチャで設定されたパスワード
    }
    
    # APIリクエスト（フォームデータとして送信）
    response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data  # OAuth2PasswordRequestFormはフォームデータを期待する
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_nonexistent_user(db_session, async_client):
    """
    異常系テスト：存在しないユーザー名でログインするとエラーになることを確認
    """
    # テストデータ（存在しないユーザー）
    login_data = {
        "username": "nonexistent_user",
        "password": "test_password123"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data
    assert "ユーザー名またはパスワードが正しくありません" in error_data["detail"]


@pytest.mark.asyncio
async def test_login_wrong_password(db_session, test_user, async_client):
    """
    異常系テスト：間違ったパスワードでログインするとエラーになることを確認
    """
    # テストデータ（正しいユーザー名、間違ったパスワード）
    login_data = {
        "username": test_user.username,
        "password": "wrong_password"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data
    assert "ユーザー名またはパスワードが正しくありません" in error_data["detail"]
