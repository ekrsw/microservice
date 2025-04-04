# 正常系テスト
import pytest
from app.core.security import verify_password
from app.crud.user import user
from app.schemas.user import UserCreate, UserUpdate


# Create操作テスト
@pytest.mark.asyncio
async def test_create_user(db_session, unique_username):
    # db_sessionがテスト用DBへの接続を提供
    user_in = UserCreate(
        username=unique_username,
        password="password123"
    )
    
    # ユーザー作成
    db_user = await user.create(db_session, user_in)
    
    # 基本的な検証
    assert db_user.id is not None
    assert db_user.username == unique_username

    # DBから取得して検証
    result = await user.get_by_id(db_session, db_user.id)
    assert result is not None
    assert result.username == unique_username

    # パスワードの検証
    assert result.hashed_password != "password123"
    assert await verify_password("password123", result.hashed_password)
    assert not await verify_password("wrongpassword", result.hashed_password)

    # ユーザーの削除
    await db_session.delete(result)
    await db_session.commit()
    # DBから削除されたことを確認
    result = await user.get_by_id(db_session, db_user.id)
    assert result is None


# Read操作テスト
@pytest.mark.asyncio
async def test_get_user_by_id_exists(db_session, unique_username):
    # ユーザーを作成
    user_in = UserCreate(
        username=unique_username,
        password="password123"
    )
    db_user = await user.create(db_session, user_in)

    # IDでユーザーを取得して検証
    found_user = await user.get_by_id(db_session, db_user.id)
    assert found_user is not None
    assert found_user.id == db_user.id
    assert found_user.username == unique_username

    # ユーザーの削除
    await db_session.delete(found_user)
    await db_session.commit()
    # DBから削除されたことを確認
    found_user = await user.get_by_id(db_session, db_user.id)
    assert found_user is None

@pytest.mark.asyncio
async def test_get_user_by_username_exists(db_session):
    # ユーザー作成
    user_in = UserCreate(username="findme", password="password123")
    await user.create(db_session, user_in)
    
    # ユーザー名で検索
    found_user = await user.get_by_username(db_session, "findme")
    assert found_user is not None
    assert found_user.username == "findme"

    # ユーザー名が存在しない場合
    not_exist_user = await user.get_by_username(db_session, "nonexistent")
    assert not_exist_user is None

    # ユーザーの削除
    await db_session.delete(found_user)
    await db_session.commit()
    # DBから削除されたことを確認
    found_user = await user.get_by_username(db_session, "findme")
    assert found_user is None

# Update操作テスト
@pytest.mark.asyncio
async def test_update_username(db_session):
    # ユーザー作成
    user_in = UserCreate(username="oldname", password="password123")
    db_user = await user.create(db_session, user_in)
    
    # ユーザー名更新
    user_update = UserUpdate(username="newname")
    updated_user = await user.update(db_session, db_user, user_update)
    
    # 更新確認
    assert updated_user.username == "newname"
    
    # DBから再取得して確認
    db_updated = await user.get_by_id(db_session, db_user.id)
    assert db_updated.username == "newname"

    # ユーザーの削除
    await db_session.delete(db_updated)
    await db_session.commit()
    # DBから削除されたことを確認
    db_updated = await user.get_by_id(db_session, db_user.id)
    assert db_updated is None

@pytest.mark.asyncio
async def test_update_password(db_session):
    # ユーザー作成
    user_in = UserCreate(username="pwduser", password="oldpassword")
    db_user = await user.create(db_session, user_in)
    
    # パスワード更新
    user_update = UserUpdate(password="newpassword")
    updated_user = await user.update(db_session, db_user, user_update)
    
    # パスワードが更新されていることを確認
    assert await verify_password("newpassword", updated_user.hashed_password)
    assert not await verify_password("oldpassword", updated_user.hashed_password)

    # DBから再取得して確認
    db_updated = await user.get_by_id(db_session, db_user.id)
    assert await verify_password("newpassword", db_updated.hashed_password)
    assert not await verify_password("oldpassword", db_updated.hashed_password)

    # ユーザーの削除
    await db_session.delete(db_updated)
    await db_session.commit()
    # DBから削除されたことを確認
    db_updated = await user.get_by_id(db_session, db_user.id)
    assert db_updated is None

# Delete操作テスト
@pytest.mark.asyncio
async def test_delete_user(db_session):
    # ユーザー作成
    user_in = UserCreate(username="deleteuser", password="password123")
    db_user = await user.create(db_session, user_in)
    
    # ユーザー削除
    await user.delete(db_session, db_user)
    
    # 削除確認
    found_user = await user.get_by_id(db_session, db_user.id)
    assert found_user is None