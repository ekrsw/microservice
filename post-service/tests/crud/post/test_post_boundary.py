# 境界値テスト
import pytest
import uuid
from datetime import datetime

from app.crud.post import post
from app.schemas.post import PostCreate, PostUpdate


@pytest.mark.asyncio
async def test_create_post_with_long_title(db_session, mock_current_user):
    """非常に長いタイトルを持つ投稿の作成テスト"""
    # 255文字のタイトル（SQLAlchemyのString型のデフォルト最大長）
    long_title = "あ" * 255
    
    post_in = PostCreate(
        title=long_title,
        content="通常の内容",
        is_published=True
    )
    
    # 投稿作成
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    
    # 検証
    assert db_post.id is not None
    assert db_post.title == long_title
    assert len(db_post.title) == 255
    
    # DBから取得して検証
    result = await post.get(db_session, id=db_post.id)
    assert result is not None
    assert result.title == long_title
    assert len(result.title) == 255

@pytest.mark.asyncio
async def test_create_post_with_long_content(db_session, mock_current_user):
    """非常に長い内容を持つ投稿の作成テスト"""
    # 10000文字の内容
    long_content = "あ" * 10000
    
    post_in = PostCreate(
        title="通常のタイトル",
        content=long_content,
        is_published=True
    )
    
    # 投稿作成
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    
    # 検証
    assert db_post.id is not None
    assert db_post.content == long_content
    assert len(db_post.content) == 10000
    
    # DBから取得して検証
    result = await post.get(db_session, id=db_post.id)
    assert result is not None
    assert result.content == long_content
    assert len(result.content) == 10000

@pytest.mark.asyncio
async def test_create_post_with_special_chars(db_session, mock_current_user):
    """特殊文字を含むタイトルと内容を持つ投稿の作成テスト"""
    special_title = "特殊文字!@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`"
    special_content = """複数行の特殊文字を含む内容
    改行
    タブ\t
    特殊文字!@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`
    日本語も含む😊絵文字も🎉
    """
    
    post_in = PostCreate(
        title=special_title,
        content=special_content,
        is_published=True
    )
    
    # 投稿作成
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    
    # 検証
    assert db_post.id is not None
    assert db_post.title == special_title
    assert db_post.content == special_content
    
    # DBから取得して検証
    result = await post.get(db_session, id=db_post.id)
    assert result is not None
    assert result.title == special_title
    assert result.content == special_content

@pytest.mark.asyncio
async def test_create_post_with_empty_content(db_session, mock_current_user):
    """内容が空の投稿の作成テスト"""
    post_in = PostCreate(
        title="内容なしの投稿",
        content=None,  # 内容なし
        is_published=True
    )
    
    # 投稿作成
    db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    
    # 検証
    assert db_post.id is not None
    assert db_post.title == "内容なしの投稿"
    assert db_post.content is None
    
    # DBから取得して検証
    result = await post.get(db_session, id=db_post.id)
    assert result is not None
    assert result.title == "内容なしの投稿"
    assert result.content is None

@pytest.mark.asyncio
async def test_update_post_with_long_title(db_session, test_post):
    """投稿タイトルを非常に長いものに更新するテスト"""
    # 255文字のタイトル
    long_title = "あ" * 255
    
    # タイトル更新
    post_update = PostUpdate(title=long_title)
    updated_post = await post.update(db_session, db_obj=test_post, obj_in=post_update)
    
    # 検証
    assert updated_post.title == long_title
    assert len(updated_post.title) == 255
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_post.id)
    assert db_updated.title == long_title
    assert len(db_updated.title) == 255

@pytest.mark.asyncio
async def test_update_post_with_long_content(db_session, test_post):
    """投稿内容を非常に長いものに更新するテスト"""
    # 10000文字の内容
    long_content = "あ" * 10000
    
    # 内容更新
    post_update = PostUpdate(content=long_content)
    updated_post = await post.update(db_session, db_obj=test_post, obj_in=post_update)
    
    # 検証
    assert updated_post.content == long_content
    assert len(updated_post.content) == 10000
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_post.id)
    assert db_updated.content == long_content
    assert len(db_updated.content) == 10000

@pytest.mark.asyncio
async def test_update_post_to_empty_content(db_session, test_post):
    """投稿内容を空に更新するテスト"""
    # 内容を空に更新
    post_update = PostUpdate(content=None)
    updated_post = await post.update(db_session, db_obj=test_post, obj_in=post_update)
    
    # 検証
    assert updated_post.content is None
    
    # DBから再取得して確認
    db_updated = await post.get(db_session, id=test_post.id)
    assert db_updated.content is None

@pytest.mark.asyncio
async def test_get_posts_with_pagination(db_session, mock_current_user):
    """ページネーションを使用した投稿取得テスト"""
    # 複数の投稿を作成
    for i in range(5):
        post_in = PostCreate(
            title=f"ページネーションテスト投稿 {i+1}",
            content=f"これはページネーションテスト用の投稿 {i+1} です。",
            is_published=True
        )
        await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
    
    # 最初の2件を取得
    posts_page1 = await post.get_multi(db_session, skip=0, limit=2, published_only=True)
    
    # 検証
    assert len(posts_page1) == 2
    
    # 次の2件を取得
    posts_page2 = await post.get_multi(db_session, skip=2, limit=2, published_only=True)
    
    # 検証
    assert len(posts_page2) == 2
    
    # 重複がないことを確認
    page1_ids = [p.id for p in posts_page1]
    page2_ids = [p.id for p in posts_page2]
    assert not any(pid in page2_ids for pid in page1_ids)
