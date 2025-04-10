# パスワード更新テスト
import pytest
import uuid
from app.core.security import verify_password
from app.crud.user import user
from app.schemas.user import UserCreate, AdminUserCreate, UserUpdate


@pytest.mark.asyncio
async def test_update_password_method(db_session):
    """
    update_passwordメソッドを使用してパスワードを更新するテスト
    """
    # ユーザー作成
    user_in = UserCreate(
        username="pwduser",
        password="oldpassword"
        )
    db_user = await user.create(db_session, user_in)
    
    # パスワード更新（専用メソッドを使用）
    updated_user = await user.update_password(db_session, db_user, "newpassword")
    
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


@pytest.mark.asyncio
async def test_update_method_separate_from_password(db_session):
    """
    UserUpdateスキーマとupdate_passwordメソッドが分離されていることを確認するテスト
    """
    # ユーザー作成（一意のユーザー名を使用）
    username = f"pwduser_{uuid.uuid4()}"
    user_in = UserCreate(
        username=username,
        password="original_password"
    )
    db_user = await user.create(db_session, user_in)
    
    # ユーザー名のみ更新
    user_update = UserUpdate(username=f"updated_{username}")
    updated_user = await user.update(db_session, db_user, user_update)
    
    # ユーザー名が更新されていることを確認
    assert updated_user.username == f"updated_{username}"
    
    # パスワードは変更されていないことを確認
    assert await verify_password("original_password", updated_user.hashed_password)

    # パスワードを別途更新
    updated_user = await user.update_password(db_session, updated_user, "new_password")
    
    # パスワードが更新されていることを確認
    assert await verify_password("new_password", updated_user.hashed_password)
    assert not await verify_password("original_password", updated_user.hashed_password)

    # DBから再取得して確認
    db_updated = await user.get_by_id(db_session, db_user.id)
    assert db_updated.username == f"updated_{username}"
    assert await verify_password("new_password", db_updated.hashed_password)

    # ユーザーの削除
    await db_session.delete(db_updated)
    await db_session.commit()
    # DBから削除されたことを確認
    db_updated = await user.get_by_id(db_session, db_user.id)
    assert db_updated is None
