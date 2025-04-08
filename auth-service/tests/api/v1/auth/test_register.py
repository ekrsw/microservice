import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.crud.user import user
from app.schemas.user import UserCreate
from app.core.security import create_access_token


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
    assert data["is_active"] is True
    assert data["is_admin"] is False
    
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


@pytest.mark.asyncio
async def test_register_admin_user_by_unauthenticated_user_forbidden(db_session, async_client, unique_username):
    """
    異常系テスト：認証されていないユーザーがis_admin=Trueでユーザーを登録しようとするとエラーになることを確認
    """
    # 管理者ユーザーとして登録しようとするデータ
    admin_user_data = {
        "username": unique_username,
        "password": "test_password123",
        "is_admin": True
    }
    
    # 認証なしでリクエスト
    response = await async_client.post("/api/v1/auth/register", json=admin_user_data)
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "管理者ユーザーを登録する権限がありません" in error_data["detail"]


@pytest.mark.asyncio
async def test_register_admin_user_by_regular_user_forbidden(db_session, test_user, async_client, unique_username):
    """
    異常系テスト：一般ユーザーがis_admin=Trueでユーザーを登録しようとするとエラーになることを確認
    """
    # 一般ユーザー用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 管理者ユーザーとして登録しようとするデータ
    admin_user_data = {
        "username": unique_username,
        "password": "test_password123",
        "is_admin": True
    }
    
    # 一般ユーザーの認証でリクエスト
    response = await async_client.post(
        "/api/v1/auth/register", 
        json=admin_user_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "管理者ユーザーを登録する権限がありません" in error_data["detail"]


@pytest.mark.asyncio
async def test_register_admin_user_by_admin_success(db_session, admin_user, async_client, unique_username):
    """
    正常系テスト：管理者ユーザーがis_admin=Trueでユーザーを登録できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 新しい管理者ユーザーとして登録するデータ
    new_admin_user_data = {
        "username": unique_username,
        "password": "test_password123",
        "is_admin": True
    }
    
    # 管理者の認証でリクエスト
    response = await async_client.post(
        "/api/v1/auth/register", 
        json=new_admin_user_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == unique_username
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_admin"] is True
    
    # IDがUUIDフォーマットであることを確認
    try:
        uuid.UUID(data["id"])
    except ValueError:
        assert False, "IDはUUID形式ではありません"
