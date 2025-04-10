import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from app.main import app
from app.crud.post import post
from app.api.deps import get_current_user, get_user_post


@pytest.mark.asyncio
async def test_delete_post_success(db_session, test_post, async_client, mock_jwt_token):
    """
    正常系テスト：所有者が投稿を削除できることを確認
    """
    # 投稿の所有者として認証をモック
    owner_user = {"user_id": test_post.user_id, "payload": {"sub": str(test_post.user_id)}}
    app.dependency_overrides[get_current_user] = lambda: owner_user
    
    # get_user_postの依存関係もオーバーライド
    app.dependency_overrides[get_user_post] = lambda post_id, current_user=None, db=None: test_post
    
    # APIリクエスト
    response = await async_client.delete(
        f"/api/v1/posts/{test_post.id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_post.id)
    assert data["title"] == test_post.title
    assert data["content"] == test_post.content
    
    # DBから削除されていることを確認
    db_post = await post.get(db_session, id=test_post.id)
    assert db_post is None
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_delete_post_unauthorized(db_session, test_post, async_client):
    """
    異常系テスト：認証なしで投稿を削除しようとするとエラーになることを確認
    """
    # 認証なしでAPIリクエスト
    response = await async_client.delete(
        f"/api/v1/posts/{test_post.id}"
    )
    
    # レスポンスの検証 - 401エラーになるはず
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error_data = response.json()
    assert "detail" in error_data
    
    # DBから削除されていないことを確認
    db_post = await post.get(db_session, id=test_post.id)
    assert db_post is not None


@pytest.mark.asyncio
async def test_delete_post_by_other_user(db_session, test_post, async_client, mock_jwt_token):
    """
    異常系テスト：他のユーザーが投稿を削除しようとするとエラーになることを確認
    """
    # 別のユーザーとして認証をモック
    other_user_id = uuid.uuid4()
    other_user = {"user_id": other_user_id, "payload": {"sub": str(other_user_id)}}
    app.dependency_overrides[get_current_user] = lambda: other_user
    
    # get_user_postの依存関係はオーバーライドしない（実際の所有権チェックを行う）
    
    # APIリクエスト
    response = await async_client.delete(
        f"/api/v1/posts/{test_post.id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証 - 403エラーになるはず
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    
    # DBから削除されていないことを確認
    db_post = await post.get(db_session, id=test_post.id)
    assert db_post is not None
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_delete_nonexistent_post(db_session, mock_current_user, async_client, mock_jwt_token):
    """
    異常系テスト：存在しない投稿を削除しようとするとエラーになることを確認
    """
    # 認証をモック
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    
    # 存在しないUUID
    nonexistent_id = uuid.uuid4()
    
    # APIリクエスト
    response = await async_client.delete(
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
async def test_delete_published_post(db_session, test_post, async_client, mock_jwt_token):
    """
    正常系テスト：公開済みの投稿を削除できることを確認
    """
    # 投稿が公開済みであることを確認
    assert test_post.is_published is True
    
    # 投稿の所有者として認証をモック
    owner_user = {"user_id": test_post.user_id, "payload": {"sub": str(test_post.user_id)}}
    app.dependency_overrides[get_current_user] = lambda: owner_user
    
    # get_user_postの依存関係もオーバーライド
    app.dependency_overrides[get_user_post] = lambda post_id, current_user=None, db=None: test_post
    
    # APIリクエスト
    response = await async_client.delete(
        f"/api/v1/posts/{test_post.id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    
    # DBから削除されていることを確認
    db_post = await post.get(db_session, id=test_post.id)
    assert db_post is None
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_delete_unpublished_post(db_session, test_unpublished_post, async_client, mock_jwt_token):
    """
    正常系テスト：非公開の投稿を削除できることを確認
    """
    # 投稿が非公開であることを確認
    assert test_unpublished_post.is_published is False
    
    # 投稿の所有者として認証をモック
    owner_user = {"user_id": test_unpublished_post.user_id, "payload": {"sub": str(test_unpublished_post.user_id)}}
    app.dependency_overrides[get_current_user] = lambda: owner_user
    
    # get_user_postの依存関係もオーバーライド
    app.dependency_overrides[get_user_post] = lambda post_id, current_user=None, db=None: test_unpublished_post
    
    # APIリクエスト
    response = await async_client.delete(
        f"/api/v1/posts/{test_unpublished_post.id}",
        headers={"Authorization": f"Bearer {mock_jwt_token}"}
    )
    
    # レスポンスの検証
    assert response.status_code == status.HTTP_200_OK
    
    # DBから削除されていることを確認
    db_post = await post.get(db_session, id=test_unpublished_post.id)
    assert db_post is None
    
    # 依存関係のオーバーライドをリセット
    app.dependency_overrides = {}
