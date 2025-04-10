import pytest
from httpx import AsyncClient
from fastapi import status
import uuid
from unittest.mock import patch, MagicMock

from app.main import app
from app.crud.post import post
from app.schemas.post import PostCreate
from app.api.deps import get_current_user


@pytest.mark.asyncio
async def test_create_post_success(db_session, mock_current_user, async_client, mock_jwt_token):
    """
    正常系テスト：認証済みユーザーが正常に投稿を作成できることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # テストデータ
    test_post_data = {
        "title": "テスト投稿",
        "content": "これはテスト投稿の内容です。",
        "is_published": True
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/posts/",
        json=test_post_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "テスト投稿"
    assert data["content"] == "これはテスト投稿の内容です。"
    assert data["is_published"] is True
    assert "id" in data
    assert "user_id" in data
    assert data["user_id"] == str(mock_current_user["user_id"])
    
    # IDがUUIDフォーマットであることを確認
    try:
        uuid.UUID(data["id"])
    except ValueError:
        assert False, "IDはUUID形式ではありません"
    
    # DBに保存されていることを確認
    db_post = await post.get(db_session, id=uuid.UUID(data["id"]))
    assert db_post is not None
    assert db_post.title == "テスト投稿"
    assert db_post.content == "これはテスト投稿の内容です。"
    assert db_post.is_published is True
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_create_post_unauthorized(async_client):
    """
    異常系テスト：認証なしで投稿を作成しようとするとエラーになることを確認
    """
    # テストデータ
    test_post_data = {
        "title": "認証なし投稿",
        "content": "これは認証なしの投稿です。",
        "is_published": True
    }
    
    # 認証なしでAPIリクエスト
    response = await async_client.post(
        "/api/v1/posts/",
        json=test_post_data
    )
    
    # レスポンスの検証 - 401エラーになるはず
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.asyncio
async def test_create_post_invalid_data(db_session, mock_current_user, async_client, mock_jwt_token):
    """
    異常系テスト：無効なデータで投稿を作成しようとするとエラーになることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # 無効なテストデータ（タイトルなし）
    invalid_post_data = {
        "content": "これはタイトルなしの投稿です。",
        "is_published": True
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/posts/",
        json=invalid_post_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証 - 422エラーになるはず
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_data = response.json()
    assert "detail" in error_data
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_create_unpublished_post(db_session, mock_current_user, async_client, mock_jwt_token):
    """
    正常系テスト：非公開投稿を作成できることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # テストデータ（非公開）
    test_post_data = {
        "title": "非公開テスト投稿",
        "content": "これは非公開のテスト投稿です。",
        "is_published": False
    }
    
    # APIリクエスト
    response = await async_client.post(
        "/api/v1/posts/",
        json=test_post_data,
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "非公開テスト投稿"
    assert data["content"] == "これは非公開のテスト投稿です。"
    assert data["is_published"] is False
    assert data["published_at"] is None
    
    # DBに保存されていることを確認
    db_post = await post.get(db_session, id=uuid.UUID(data["id"]))
    assert db_post is not None
    assert db_post.title == "非公開テスト投稿"
    assert db_post.is_published is False
    assert db_post.published_at is None
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}
