import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_update_self_success(db_session, test_user, async_client):
    """
    正常系テスト：ユーザーが自分自身の情報を更新できることを確認
    """
    # アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 更新データ
    update_data = {
        "username": f"updated_{test_user.username}"
    }
    
    # APIリクエスト
    response = await async_client.put(
        f"/api/v1/auth/users/{test_user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["username"] == update_data["username"]
    assert updated_user["is_admin"] == test_user.is_admin  # 変更していないフィールドは元の値のまま

@pytest.mark.asyncio
async def test_admin_update_other_user_success(db_session, admin_user, test_user, async_client):
    """
    正常系テスト：管理者ユーザーが他のユーザーの情報を更新できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 更新データ
    update_data = {
        "username": f"updated_by_admin",  # 短いユーザー名に変更
        "is_active": False
    }
    
    # APIリクエスト
    response = await async_client.put(
        f"/api/v1/auth/users/{test_user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["username"] == update_data["username"]
    assert updated_user["is_active"] == update_data["is_active"]

@pytest.mark.asyncio
async def test_admin_update_admin_flag_success(db_session, admin_user, test_user, async_client):
    """
    正常系テスト：管理者ユーザーがis_adminフラグを変更できることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 更新データ
    update_data = {
        "is_admin": True
    }
    
    # APIリクエスト
    response = await async_client.put(
        f"/api/v1/auth/users/{test_user.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["is_admin"] == True

@pytest.mark.asyncio
async def test_regular_user_update_other_user_forbidden(db_session, test_user, admin_user, async_client):
    """
    異常系テスト：一般ユーザーが他のユーザーの更新を試みると403エラーになることを確認
    """
    # 一般ユーザー用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 更新データ
    update_data = {
        "username": "should_not_update"
    }
    
    # APIリクエスト
    response = await async_client.put(
        f"/api/v1/auth/users/{admin_user.id}",  # 別のユーザーのID
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "他のユーザーを更新する権限がありません" in error_data["detail"]

@pytest.mark.asyncio
async def test_regular_user_update_admin_flag_forbidden(db_session, test_user, async_client):
    """
    異常系テスト：一般ユーザーがis_adminフラグの変更を試みると403エラーになることを確認
    """
    # 一般ユーザー用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 更新データ
    update_data = {
        "is_admin": True
    }
    
    # APIリクエスト
    response = await async_client.put(
        f"/api/v1/auth/users/{test_user.id}",  # 自分自身のID
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "管理者権限を変更する権限がありません" in error_data["detail"]

@pytest.mark.asyncio
async def test_update_nonexistent_user_not_found(db_session, admin_user, async_client):
    """
    異常系テスト：存在しないユーザーIDで更新を試みると404エラーになることを確認
    """
    # 管理者用アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(admin_user.id)}
    )
    
    # 存在しないUUID
    nonexistent_id = str(uuid.uuid4())
    
    # 更新データ
    update_data = {
        "username": "nonexistent_user"
    }
    
    # APIリクエスト
    response = await async_client.put(
        f"/api/v1/auth/users/{nonexistent_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "detail" in error_data
    assert "指定されたユーザーが見つかりません" in error_data["detail"]
