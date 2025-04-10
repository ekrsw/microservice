# 正常系テスト
import pytest
from datetime import datetime
from uuid import UUID

from app.crud.post import post
from app.schemas.post import PostCreate, PostUpdate


# Create操作テスト
@pytest.mark.asyncio
async def test_create_post(db_session, mock_current_user):
    """投稿作成の基本テスト"""
    # 投稿データ作成
    post_in = PostCreate(
        title="テスト投稿",
        content="これはテスト投稿の内容です。",
        is_published=True
    )
    
    # 投稿作成
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    
    # 基本的な検証
    assert db_post.id is not None
    assert db_post.title == "テスト投稿"
    assert db_post.content == "これはテスト投稿の内容です。"
    assert db_post.is_published is True
    assert db_post.user_id == mock_current_user["user_id"]
    assert db_post.published_at is not None

    # DBから取得して検証
    result = await post.get(db_session, id=db_post.id)
    assert result is not None
    assert result.title == "テスト投稿"
    assert result.content == "これはテスト投稿の内容です。"
    assert result.is_published is True
    assert result.user_id == mock_current_user["user_id"]

@pytest.mark.asyncio
async def test_create_unpublished_post(db_session, mock_current_user):
    """非公開投稿作成のテスト"""
    # 投稿データ作成（非公開）
    post_in = PostCreate(
        title="非公開投稿",
        content="これは非公開の投稿です。",
        is_published=False
    )
    
    # 投稿作成
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    
    # 検証
    assert db_post.is_published is False
    assert db_post.published_at is None

    # DBから取得して検証
    result = await post.get(db_session, id=db_post.id)
    assert result is not None
    assert result.is_published is False
    assert result.published_at is None

# Read操作テスト
@pytest.mark.asyncio
async def test_get_post_by_id(db_session, test_post):
    """IDによる投稿取得テスト"""
    # IDで投稿を取得
    found_post = await post.get(db_session, id=test_post.id)
    
    # 検証
    assert found_post is not None
    assert found_post.id == test_post.id
    assert found_post.title == test_post.title
    assert found_post.content == test_post.content
    assert found_post.user_id == test_post.user_id
    assert found_post.is_published == test_post.is_published

@pytest.mark.asyncio
async def test_get_multi_posts(db_session, test_post, test_unpublished_post):
    """複数投稿取得テスト"""
    # 公開投稿のみ取得
    posts = await post.get_multi(db_session, published_only=True)
    
    # 検証
    assert len(posts) >= 1
    # test_postは公開されているので含まれるはず
    assert any(p.id == test_post.id for p in posts)
    # test_unpublished_postは非公開なので含まれないはず
    assert not any(p.id == test_unpublished_post.id for p in posts)
    
    # 全投稿取得
    all_posts = await post.get_multi(db_session, published_only=False)
    
    # 検証
    assert len(all_posts) >= 2
    # 両方の投稿が含まれるはず
    assert any(p.id == test_post.id for p in all_posts)
    assert any(p.id == test_unpublished_post.id for p in all_posts)

@pytest.mark.asyncio
async def test_get_posts_by_user(db_session, test_post, test_unpublished_post):
    """ユーザー別投稿取得テスト"""
    user_id = test_post.user_id
    
    # 特定ユーザーの公開投稿のみ取得
    posts = await post.get_by_user(db_session, user_id=user_id, published_only=True)
    
    # 検証
    assert len(posts) >= 1
    assert any(p.id == test_post.id for p in posts)
    assert not any(p.id == test_unpublished_post.id for p in posts)
    
    # 特定ユーザーの全投稿取得
    all_posts = await post.get_by_user(db_session, user_id=user_id, published_only=False)
    
    # 検証
    assert len(all_posts) >= 2
    assert any(p.id == test_post.id for p in all_posts)
    assert any(p.id == test_unpublished_post.id for p in all_posts)

# Update操作テスト
@pytest.mark.asyncio
async def test_update_post_title(db_session, test_post):
    """投稿タイトル更新テスト"""
    # タイトル更新
    post_update = PostUpdate(title="更新されたタイトル")
    updated_post = await post.update(db_session, db_obj=test_post, obj_in=post_update)
    
    # 検証
    assert updated_post.title == "更新されたタイトル"
    assert updated_post.content == test_post.content  # 他のフィールドは変更なし
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_post.id)
    assert db_updated.title == "更新されたタイトル"

@pytest.mark.asyncio
async def test_update_post_content(db_session, test_post):
    """投稿内容更新テスト"""
    # 内容更新
    post_update = PostUpdate(content="更新された内容です。")
    updated_post = await post.update(db_session, db_obj=test_post, obj_in=post_update)
    
    # 検証
    assert updated_post.content == "更新された内容です。"
    assert updated_post.title == test_post.title  # 他のフィールドは変更なし
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_post.id)
    assert db_updated.content == "更新された内容です。"

@pytest.mark.asyncio
async def test_update_post_publish_status(db_session, test_unpublished_post):
    """投稿公開状態更新テスト"""
    # 非公開から公開に変更
    post_update = PostUpdate(is_published=True)
    updated_post = await post.update(db_session, db_obj=test_unpublished_post, obj_in=post_update)
    
    # 検証
    assert updated_post.is_published is True
    assert updated_post.published_at is not None
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_unpublished_post.id)
    assert db_updated.is_published is True
    assert db_updated.published_at is not None
    
    # 公開から非公開に変更
    post_update = PostUpdate(is_published=False)
    updated_post = await post.update(db_session, db_obj=db_updated, obj_in=post_update)
    
    # 検証
    assert updated_post.is_published is False
    assert updated_post.published_at is None
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_unpublished_post.id)
    assert db_updated.is_published is False
    assert db_updated.published_at is None

@pytest.mark.asyncio
async def test_publish_post(db_session, test_unpublished_post):
    """投稿公開専用メソッドのテスト"""
    # 投稿を公開
    published_post = await post.publish(db_session, db_obj=test_unpublished_post, publish=True)
    
    # 検証
    assert published_post.is_published is True
    assert published_post.published_at is not None
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_unpublished_post.id)
    assert db_updated.is_published is True
    assert db_updated.published_at is not None
    
    # 投稿を非公開に
    unpublished_post = await post.publish(db_session, db_obj=db_updated, publish=False)
    
    # 検証
    assert unpublished_post.is_published is False
    assert unpublished_post.published_at is None
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_unpublished_post.id)
    assert db_updated.is_published is False
    assert db_updated.published_at is None

# Delete操作テスト
@pytest.mark.asyncio
async def test_delete_post(db_session, test_post):
    """投稿削除テスト"""
    # 投稿削除
    deleted_post = await post.delete(db_session, id=test_post.id)
    
    # 削除された投稿の検証
    assert deleted_post is not None
    assert deleted_post.id == test_post.id
    
    # 削除確認
    found_post = await post.get(db_session, id=test_post.id)
    assert found_post is None
