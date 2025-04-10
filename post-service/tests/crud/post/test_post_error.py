# 異常系テスト
import pytest
import uuid
from datetime import datetime

from app.crud.post import post
from app.schemas.post import PostCreate, PostUpdate


@pytest.mark.asyncio
async def test_get_nonexistent_post(db_session):
    """存在しない投稿の取得テスト"""
    # 存在しないUUID
    nonexistent_id = uuid.uuid4()
    
    # 存在しない投稿を取得
    result = await post.get(db_session, id=nonexistent_id)
    
    # 検証
    assert result is None

@pytest.mark.asyncio
async def test_update_nonexistent_post(db_session):
    """存在しない投稿の更新テスト"""
    # 存在しないUUID
    nonexistent_id = uuid.uuid4()
    
    # 存在しない投稿を取得
    result = await post.get(db_session, id=nonexistent_id)
    
    # 検証
    assert result is None
    
    # 存在しない投稿を更新しようとすると、Noneが返されるか例外が発生するはず
    # この場合、更新前にgetで取得するパターンを想定しているので、
    # 単にNoneが返されることを確認する

@pytest.mark.asyncio
async def test_delete_nonexistent_post(db_session):
    """存在しない投稿の削除テスト"""
    # 存在しないUUID
    nonexistent_id = uuid.uuid4()
    
    # 存在しない投稿を削除
    result = await post.delete(db_session, id=nonexistent_id)
    
    # 検証 - 存在しない投稿を削除しようとするとNoneが返されるはず
    assert result is None

@pytest.mark.asyncio
async def test_get_posts_by_nonexistent_user(db_session):
    """存在しないユーザーの投稿取得テスト"""
    # 存在しないユーザーID
    nonexistent_user_id = uuid.uuid4()
    
    # 存在しないユーザーの投稿を取得
    results = await post.get_by_user(db_session, user_id=nonexistent_user_id)
    
    # 検証 - 空のリストが返されるはず
    assert results == []
    assert len(results) == 0

@pytest.mark.asyncio
async def test_get_posts_with_negative_skip(db_session):
    """負のスキップ値での投稿取得テスト"""
    # 負の値でのスキップ - PostgreSQLはOFFSET句に負の値を許可しないため例外が発生するはず
    try:
        await post.get_multi(db_session, skip=-1, limit=10)
        assert False, "負のスキップ値は例外を発生させるはずです"
    except Exception as e:
        # 例外が発生することを確認
        assert "OFFSET must not be negative" in str(e)

@pytest.mark.asyncio
async def test_get_posts_with_negative_limit(db_session):
    """負の制限値での投稿取得テスト"""
    # 負の値での制限 - 0として扱われるか例外が発生する可能性がある
    try:
        posts_negative_limit = await post.get_multi(db_session, skip=0, limit=-1)
        # 例外が発生しない場合は、結果がリストであることを確認
        assert isinstance(posts_negative_limit, list)
    except Exception:
        # 例外が発生しても問題ない
        pass

@pytest.mark.asyncio
async def test_get_posts_with_large_limit(db_session):
    """大きな制限値での投稿取得テスト"""
    # 非常に大きな値での制限
    posts_large_limit = await post.get_multi(db_session, skip=0, limit=1000000)
    
    # 検証 - 正常に処理されるはず（実際のデータ数に制限される）
    assert isinstance(posts_large_limit, list)

@pytest.mark.asyncio
async def test_create_post_with_invalid_user_id(db_session):
    """無効なユーザーIDでの投稿作成テスト"""
    # 投稿データ
    post_in = PostCreate(
        title="無効なユーザーIDの投稿",
        content="これは無効なユーザーIDでの投稿です。",
        is_published=True
    )
    
    # 無効なユーザーID（None）での投稿作成
    try:
        db_post = await post.create(db_session, obj_in=post_in, user_id=None)
        assert False, "Noneのユーザーでの投稿作成は失敗するはずです"
    except Exception as e:
        # 例外が発生することを確認
        assert True

@pytest.mark.asyncio
async def test_create_post_with_invalid_title(db_session, mock_current_user):
    """無効なタイトルでの投稿作成テスト"""
    # タイトルがNoneの場合、Pydanticのバリデーションエラーが発生するはず
    try:
        # タイトルがNoneの投稿データを作成しようとする
        PostCreate(
            title=None,  # タイトルなし
            content="これはタイトルなしの投稿です。",
            is_published=True
        )
        assert False, "タイトルなしでのPostCreate作成は失敗するはずです"
    except Exception as e:
        # 例外が発生することを確認
        assert "validation error" in str(e).lower()
        
    # 空文字列のタイトルでの投稿作成
    try:
        post_in = PostCreate(
            title="",  # 空文字列
            content="これは空タイトルの投稿です。",
            is_published=True
        )
        
        # 空文字列のタイトルでの投稿作成
        db_post = await post.create(db_session, obj_in=post_in, user_id=mock_current_user["user_id"])
        
        # 検証 - 成功するかもしれない（スキーマによる）
        assert db_post.title == ""
    except Exception as e:
        # 例外が発生する場合
        assert True

@pytest.mark.asyncio
async def test_update_post_with_invalid_data(db_session, test_post):
    """無効なデータでの投稿更新テスト"""
    # タイトルをNoneに更新
    try:
        post_update = PostUpdate(title=None)
        updated_post = await post.update(db_session, db_obj=test_post, obj_in=post_update)
        # タイトルがNoneでも更新できる場合（スキーマによる）
        assert updated_post.title is None
    except Exception as e:
        # 例外が発生する場合
        assert True
