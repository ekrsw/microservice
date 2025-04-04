# 境界値テスト
# ユーザー名とパスワードの長さに関する境界値テストを行う
# ユーザー名は1文字以上50文字以下
# パスワードは1文字以上16文字以下
# ユーザー名に特殊文字やUnicode文字を含む場合のテストも含む
import pytest
from app.crud.user import user
from app.schemas.user import UserCreate
from app.core.security import verify_password

@pytest.mark.asyncio
async def test_create_user_with_minimum_length_username(db_session):
    """ユーザー名が最小長（1文字）の場合のテスト"""
    user_in = UserCreate(
        username="a",  # 1文字
        password="validpassword123"
    )
    
    db_obj = await user.create(db_session, user_in)
    assert db_obj.username == "a"
    
    # データベースから取得して確認
    result = await user.get_by_username(db_session, "a")
    assert result is not None
    assert result.username == "a"
    
    # クリーンアップ
    await db_session.delete(result)
    await db_session.commit()

    # ユーザーが削除されたか確認
    result = await user.get_by_username(db_session, "a")
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_maximum_length_username(db_session):
    """ユーザー名が最大長（50文字）の場合のテスト"""
    max_length_username = "a" * 50
    user_in = UserCreate(
        username=max_length_username,
        password="validpassword123"
    )
    
    db_obj = await user.create(db_session, user_in)
    assert db_obj.username == max_length_username
    assert len(db_obj.username) == 50
    
    # データベースから取得して確認
    result = await user.get_by_username(db_session, max_length_username)
    assert result is not None
    assert result.username == max_length_username
    
    # クリーンアップ
    await db_session.delete(result)
    await db_session.commit()

    # ユーザーが削除されたか確認
    result = await user.get_by_username(db_session, max_length_username)
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_minimum_length_password(db_session):
    """パスワードが最小長（1文字）の場合のテスト"""
    user_in = UserCreate(
        username="testuser",
        password="a"  # 1文字
    )
    
    db_obj = await user.create(db_session, user_in)
    assert await verify_password("a", db_obj.hashed_password)
    
    # クリーンアップ
    await db_session.delete(db_obj)
    await db_session.commit()

    # ユーザーが削除されたか確認
    result = await user.get_by_username(db_session, "testuser")
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_maximum_length_password(db_session):
    """パスワードが最大長（16文字）の場合のテスト"""
    max_length_password = "a" * 16
    user_in = UserCreate(
        username="testuser",
        password=max_length_password
    )
    
    db_obj = await user.create(db_session, user_in)
    assert await verify_password(max_length_password, db_obj.hashed_password)
    
    # クリーンアップ
    await db_session.delete(db_obj)
    await db_session.commit()

    # ユーザーが削除されたか確認
    result = await user.get_by_username(db_session, "testuser")
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_special_characters_in_username(db_session):
    """ユーザー名に特殊文字を含む場合のテスト"""
    special_username = "test@user#123$%^&*()_+"
    user_in = UserCreate(
        username=special_username,
        password="validpassword123"
    )
    
    db_obj = await user.create(db_session, user_in)
    assert db_obj.username == special_username
    
    # データベースから取得して確認
    result = await user.get_by_username(db_session, special_username)
    assert result is not None
    assert result.username == special_username
    
    # クリーンアップ
    await db_session.delete(result)
    await db_session.commit()

    # ユーザーが削除されたか確認
    result = await user.get_by_username(db_session, special_username)
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_unicode_characters_in_username(db_session):
    """ユーザー名にUnicode文字（日本語など）を含む場合のテスト"""
    unicode_username = "テストユーザー123"
    user_in = UserCreate(
        username=unicode_username,
        password="validpassword123"
    )
    
    db_obj = await user.create(db_session, user_in)
    assert db_obj.username == unicode_username
    
    # データベースから取得して確認
    result = await user.get_by_username(db_session, unicode_username)
    assert result is not None
    assert result.username == unicode_username
    
    # クリーンアップ
    await db_session.delete(result)
    await db_session.commit()

    # ユーザーが削除されたか確認
    result = await user.get_by_username(db_session, unicode_username)
    assert result is None