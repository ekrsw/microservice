import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.core.security import create_access_token, verify_password

@pytest.mark.asyncio
async def test_update_own_password_success(db_session, test_user, async_client):
    """
    正常系テスト：ユーザーが自分自身のパスワードを更新できることを確認
    """
    # アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 更新データ
    update_data = {
        "current_password": "test_password123",  # conftest.pyで設定された初期パスワード
        "new_password": "new_password456"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/update/password",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    updated_user = response.json()
    assert updated_user["id"] == str(test_user.id)
    
    # DBからユーザーを再取得して、パスワードが更新されていることを確認
    # 注：実際のテストでは、DBへの直接アクセスではなく、ログインなどの機能を使って間接的に確認するのが望ましい
    from app.crud.user import user
    db_user = await user.get_by_id(db_session, test_user.id)
    assert await verify_password("new_password456", db_user.hashed_password)

@pytest.mark.asyncio
async def test_update_password_wrong_current_password(db_session, test_user, async_client):
    """
    異常系テスト：現在のパスワードが間違っている場合は401エラーになることを確認
    """
    # アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 更新データ（間違ったパスワード）
    update_data = {
        "current_password": "wrong_password",
        "new_password": "new_password456"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/update/password",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data
    assert "現在のパスワードが正しくありません" in error_data["detail"]

@pytest.mark.asyncio
async def test_update_password_unauthorized(db_session, async_client):
    """
    異常系テスト：認証なしでパスワード更新を試みると401エラーになることを確認
    """
    # 更新データ
    update_data = {
        "current_password": "test_password123",
        "new_password": "new_password456"
    }
    
    # APIリクエスト（認証ヘッダーなし）
    response = await async_client.post(
        "/api/v1/auth/update/password",
        json=update_data
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data

@pytest.mark.asyncio
async def test_update_password_same_as_current(db_session, test_user, async_client):
    """
    異常系テスト：新しいパスワードが現在のパスワードと同じ場合はバリデーションエラーになることを確認
    """
    # アクセストークンの生成
    access_token = await create_access_token(
        data={"sub": str(test_user.id)}
    )
    
    # 更新データ（新しいパスワードが現在のパスワードと同じ）
    update_data = {
        "current_password": "test_password123",
        "new_password": "test_password123"
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/auth/update/password",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # レスポンスの検証
    # 注：バリデーションエラーは422または400のいずれかになる可能性があります
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    error_data = response.json()
    assert "detail" in error_data
