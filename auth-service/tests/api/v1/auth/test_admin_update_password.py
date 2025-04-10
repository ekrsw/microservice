import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.core.security import create_access_token, verify_password

@pytest.mark.asyncio
async def test_admin_update_other_user_password_success(db_session, admin_user, test_user, async_client):
    """
    正常系テスト：管理者が他のユーザーのパスワードを更新できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 更新データ
    update_data = {
        "user_id": str(test_user.id),
        "new_password": "admin_set_password"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/admin/update/password",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    # 注：テストが失敗している場合は、レスポンスの詳細を確認
    if response.status_code != status.HTTP_200_OK:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["id"] == str(test_user.id)
    
    # DBからユーザーを再取得して、パスワードが更新されていることを確認
    from app.crud.user import user
    db_user = await user.get_by_id(db_session, test_user.id)
    assert await verify_password("admin_set_password", db_user.hashed_password)

@pytest.mark.asyncio
async def test_admin_update_own_password_success(db_session, admin_user, async_client):
    """
    正常系テスト：管理者が自分自身のパスワードを管理者エンドポイントで更新できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 更新データ
    update_data = {
        "user_id": str(admin_user.id),
        "new_password": "new_admin_password"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/admin/update/password",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["id"] == str(admin_user.id)
    
    # DBからユーザーを再取得して、パスワードが更新されていることを確認
    from app.crud.user import user
    db_user = await user.get_by_id(db_session, admin_user.id)
    assert await verify_password("new_admin_password", db_user.hashed_password)

@pytest.mark.asyncio
async def test_regular_user_cannot_use_admin_endpoint(db_session, test_user, async_client):
    """
    異常系テスト：一般ユーザーが管理者用エンドポイントを使用すると403エラーになることを確認
    """
    # 一般ユーザー用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 更新データ
    update_data = {
        "user_id": str(test_user.id),
        "new_password": "should_not_update"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/admin/update/password",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data

@pytest.mark.asyncio
async def test_admin_update_nonexistent_user_password(db_session, admin_user, async_client):
    """
    異常系テスト：存在しないユーザーIDでパスワード更新を試みると404エラーになることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 存在しないUUID
    nonexistent_id = str(uuid.uuid4())
    
    # 更新データ
    update_data = {
        "user_id": nonexistent_id,
        "new_password": "nonexistent_user_password"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/admin/update/password",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "detail" in error_data
    assert "指定されたユーザーが見つかりません" in error_data["detail"]

@pytest.mark.asyncio
async def test_admin_update_password_unauthorized(db_session, async_client):
    """
    異常系テスト：認証なしで管理者用パスワード更新エンドポイントを使用すると401エラーになることを確認
    """
    # 更新データ
    update_data = {
        "user_id": str(uuid.uuid4()),
        "new_password": "unauthorized_password"
    }
    
    # APIリクエスト（認証ヘッダーなし）
    response = await async_client.post(
        "/api/v1/auth/admin/update/password",
        json=update_data
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data
