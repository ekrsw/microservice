import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_admin_delete_user_success(db_session, admin_user, test_user, async_client):
    """
    正常系テスト：管理者ユーザーが他のユーザーを削除できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # APIリクエスト
    response = await async_client.delete(
        f"/api/v1/auth/delete/user/{test_user.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b''  # 204 No Contentは空のレスポンスボディを返す

@pytest.mark.asyncio
async def test_admin_delete_self_forbidden(db_session, admin_user, async_client):
    """
    異常系テスト：管理者ユーザーが自分自身を削除しようとすると400エラーになることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # APIリクエスト（自分自身を削除しようとする）
    response = await async_client.delete(
        f"/api/v1/auth/delete/user/{admin_user.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error_data = response.json()
    assert "detail" in error_data
    assert "自分自身を削除することはできません" in error_data["detail"]

@pytest.mark.asyncio
async def test_regular_user_delete_forbidden(db_session, test_user, admin_user, async_client):
    """
    異常系テスト：一般ユーザーがユーザー削除を試みると403エラーになることを確認
    """
    # 一般ユーザー用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # APIリクエスト（管理者ユーザーを削除しようとする）
    response = await async_client.delete(
        f"/api/v1/auth/delete/user/{admin_user.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "この操作には管理者権限が必要です" in error_data["detail"]

@pytest.mark.asyncio
async def test_delete_nonexistent_user_not_found(db_session, admin_user, async_client):
    """
    異常系テスト：存在しないユーザーIDで削除を試みると404エラーになることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 存在しないUUID
    nonexistent_id = str(uuid.uuid4())
    
    # APIリクエスト
    response = await async_client.delete(
        f"/api/v1/auth/delete/user/{nonexistent_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "detail" in error_data
    assert "指定されたユーザーが見つかりません" in error_data["detail"]
