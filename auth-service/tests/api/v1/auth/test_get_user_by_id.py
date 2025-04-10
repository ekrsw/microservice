import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_get_self_success(db_session, test_user, async_client):
    """
    正常系テスト：ユーザーが自分自身の情報を取得できることを確認
    """
    # アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/auth/user/{test_user.id}",
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
async def test_admin_get_other_user_success(db_session, admin_user, test_user, async_client):
    """
    正常系テスト：管理者ユーザーが他のユーザーの情報を取得できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/auth/user/{test_user.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["id"] == str(test_user.id)
    assert user_data["username"] == test_user.username

@pytest.mark.asyncio
async def test_regular_user_get_other_user_forbidden(db_session, test_user, admin_user, async_client):
    """
    異常系テスト：一般ユーザーが他のユーザーの情報取得を試みると403エラーになることを確認
    """
    # 一般ユーザー用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # APIリクエスト（別のユーザーの情報を取得しようとする）
    response = await async_client.get(
        f"/api/v1/auth/user/{admin_user.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "他のユーザー情報を取得する権限がありません" in error_data["detail"]

@pytest.mark.asyncio
async def test_get_nonexistent_user_not_found(db_session, admin_user, async_client):
    """
    異常系テスト：存在しないユーザーIDで情報取得を試みると404エラーになることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 存在しないUUID
    nonexistent_id = str(uuid.uuid4())
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/auth/user/{nonexistent_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "detail" in error_data
    assert "指定されたユーザーが見つかりません" in error_data["detail"]
