import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_get_all_users_admin_success(db_session, admin_user, test_user, async_client):
    """
    正常系テスト：管理者ユーザーが全ユーザーリストを取得できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # APIリクエスト
    response = await async_client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 2  # 少なくとも管理者と一般ユーザーの2人がいるはず
    
    # レスポンスに両方のユーザーが含まれていることを確認
    user_ids = [user["id"] for user in users]
    assert str(admin_user.id) in user_ids
    assert str(test_user.id) in user_ids

@pytest.mark.asyncio
async def test_get_all_users_regular_user_forbidden(db_session, test_user, async_client):
    """
    異常系テスト：一般ユーザーが全ユーザーリストの取得を試みると403エラーになることを確認
    """
    # 一般ユーザー用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # APIリクエスト
    response = await async_client.get(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "この操作には管理者権限が必要です" in error_data["detail"]
