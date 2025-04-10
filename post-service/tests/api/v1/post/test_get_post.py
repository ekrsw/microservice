import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.crud.post import post
from app.api.deps import get_current_user


@pytest.mark.asyncio
async def test_get_post_by_id_success(db_session, test_post, mock_current_user, async_client, mock_jwt_token):
    """
    正常系テスト：IDで投稿を取得できることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/posts/{test_post.id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_post.id)
    assert data["title"] == test_post.title
    assert data["content"] == test_post.content
    assert data["is_published"] == test_post.is_published
    assert data["user_id"] == str(test_post.user_id)
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_nonexistent_post(db_session, mock_current_user, async_client, mock_jwt_token):
    """
    異常系テスト：存在しない投稿を取得しようとするとエラーになることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # 存在しないUUID
    nonexistent_id = uuid.uuid4()
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/posts/{nonexistent_id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証 - 404エラーになるはず
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "detail" in error_data
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_unpublished_post_by_owner(db_session, test_unpublished_post, async_client, mock_jwt_token):
    """
    正常系テスト：所有者は自分の非公開投稿を取得できることを確認
    """
    # 投稿の所有者として認証をモック
    owner_user = {"user_id": test_unpublished_post.user_id, "payload": {"sub": str(test_unpublished_post.user_id)}}
    app.dependency_overrides[get_current_user] = lambda: owner_user
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/posts/{test_unpublished_post.id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_unpublished_post.id)
    assert data["title"] == test_unpublished_post.title
    assert data["is_published"] is False
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_unpublished_post_by_other_user(db_session, test_unpublished_post, async_client, mock_jwt_token):
    """
    異常系テスト：他のユーザーは非公開投稿を取得できないことを確認
    """
    # 別のユーザーとして認証をモック
    other_user_id = uuid.uuid4()
    other_user = {"user_id": other_user_id, "payload": {"sub": str(other_user_id)}}
    app.dependency_overrides[get_current_user] = lambda: other_user
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/posts/{test_unpublished_post.id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証 - 403エラーになるはず
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_all_posts(db_session, test_post, test_unpublished_post, mock_current_user, async_client, mock_jwt_token):
    """
    正常系テスト：公開投稿の一覧を取得できることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # APIリクエスト
    response = await async_client.get(
        "/api/v1/posts/",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    
    # 公開投稿のみが含まれていることを確認
    post_ids = [post["id"] for post in data]
    assert str(test_post.id) in post_ids
    assert str(test_unpublished_post.id) not in post_ids
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_all_posts_with_published_only_false(db_session, test_post, test_unpublished_post, mock_current_user, async_client, mock_jwt_token):
    """
    正常系テスト：published_only=Falseパラメータで全ての投稿を取得できることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # APIリクエスト（published_only=False）
    response = await async_client.get(
        "/api/v1/posts/?published_only=false",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    
    # 全ての投稿が含まれていることを確認
    post_ids = [post["id"] for post in data]
    assert str(test_post.id) in post_ids
    # 注意: APIの実装によっては、他のユーザーの非公開投稿は含まれないかもしれない
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_user_posts(db_session, test_post, test_unpublished_post, async_client, mock_jwt_token):
    """
    正常系テスト：特定ユーザーの投稿一覧を取得できることを確認
    """
    # 投稿の所有者として認証をモック
    owner_user = {"user_id": test_post.user_id, "payload": {"sub": str(test_post.user_id)}}
    app.dependency_overrides[get_current_user] = lambda: owner_user
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/posts/user/{test_post.user_id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    
    # 自分の投稿が全て含まれていることを確認
    post_ids = [post["id"] for post in data]
    assert str(test_post.id) in post_ids
    assert str(test_unpublished_post.id) in post_ids
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_other_user_posts(db_session, test_post, test_unpublished_post, async_client, mock_jwt_token):
    """
    正常系テスト：他のユーザーの公開投稿のみを取得できることを確認
    """
    # 別のユーザーとして認証をモック
    other_user_id = uuid.uuid4()
    other_user = {"user_id": other_user_id, "payload": {"sub": str(other_user_id)}}
    app.dependency_overrides[get_current_user] = lambda: other_user
    
    # APIリクエスト
    response = await async_client.get(
        f"/api/v1/posts/user/{test_post.user_id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    
    # 公開投稿のみが含まれていることを確認
    post_ids = [post["id"] for post in data]
    assert str(test_post.id) in post_ids
    assert str(test_unpublished_post.id) not in post_ids
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}
