# 異常系テスト
import pytest
from pydantic import ValidationError
from uuid import UUID
from app.core.security import verify_password
from app.crud.user import user
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy import select


# Create操作テスト
# バリデーションエラー
@pytest.mark.asyncio
async def test_create_user_with_empty_username(db_session):
    # 空のユーザー名でUserCreateスキーマを作成
    with pytest.raises(ValueError) as exc_info:
        user_in = UserCreate(
            username="",
            password="password123"
        )

    # エラーの詳細を検証
    error = exc_info.value.errors()
    assert len(error) == 1
    assert error[0]["type"] == "string_too_short"
    assert error[0]["loc"] == ("username",)

    # データベースに新しいユーザーが作成されていないことを確認
    result = await user.get_by_username(db_session, username="")
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_too_long_username(db_session):
    # 51文字のユーザー名を生成（最大制限は50文字）
    too_long_username = "a" * 51
    
    # 長すぎるユーザー名でUserCreateスキーマを作成しようとする
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username=too_long_username,
            password="validpassword123"
        )
    
    # エラーの詳細を検証
    error = exc_info.value.errors()
    assert len(error) == 1
    assert error[0]["type"] == "string_too_long"
    assert error[0]["loc"] == ("username",)
    assert error[0]["ctx"]["max_length"] == 50

    # データベースに新しいユーザーが作成されていないことを確認
    result = await user.get_by_username(db_session, too_long_username)
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_empty_password(db_session):
    # 空のパスワードでUserCreateスキーマを作成しようとする
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="validusername",
            password=""  # 空文字列
        )
    
    # エラーの詳細を検証
    error = exc_info.value.errors()
    assert len(error) == 1
    assert error[0]["type"] == "string_too_short"
    assert error[0]["loc"] == ("password",)

    # データベースに新しいユーザーが作成されていないことを確認
    result = await user.get_by_username(db_session, "validusername")
    assert result is None

@pytest.mark.asyncio
async def test_create_user_with_too_long_password(db_session):
    # 17文字のパスワードを生成（最大制限は16文字）
    too_long_password = "a" * 17
    valid_username = "testuser"
    
    # 長すぎるパスワードでUserCreateスキーマを作成しようとする
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username=valid_username,
            password=too_long_password
        )
    
    # エラーの詳細を検証
    error = exc_info.value.errors()
    assert len(error) == 1
    assert error[0]["type"] == "string_too_long"
    assert error[0]["loc"] == ("password",)
    assert error[0]["ctx"]["max_length"] == 16

    # データベースに新しいユーザーが作成されていないことを確認
    result = await user.get_by_username(db_session, valid_username)
    assert result is None

# データベース制約エラー
@pytest.mark.asyncio
async def test_create_duplicate_username(db_session):
    # 1人目のユーザーを作成
    username = "testuser"
    first_user = UserCreate(
        username=username,
        password="password123"
    )
    await user.create(db_session, first_user)

    # 同じユーザー名で2人目のユーザーを作成しようとする
    second_user = UserCreate(
        username=username,  # 同じユーザー名
        password="diffpassword123"
    )

    # IntegrityErrorが発生することを確認
    with pytest.raises(IntegrityError) as exc_info:
        await user.create(db_session, second_user)
    
    # エラーメッセージにユニーク制約違反が含まれていることを確認
    assert "unique constraint" in str(exc_info.value).lower()

    # セッションをロールバックしてから次のクエリを実行
    await db_session.rollback()
    
    # データベースに1人目のユーザーのみが存在することを確認
    users = await db_session.execute(select(User).filter(User.username == username))
    users_list = users.scalars().all()
    assert len(users_list) == 1
    assert users_list[0].username == username

    # テストデータのクリーンアップ
    await db_session.delete(users_list[0])
    await db_session.commit()
    # DBから削除されたことを確認
    result = await user.get_by_username(db_session, username)
    assert result is None

# Read操作テスト
@pytest.mark.asyncio
async def test_get_user_by_invalid_id(db_session):
    # 無効なUUID形式の文字列
    invalid_id = "not-a-uuid"
    
    # 無効なUUIDでユーザーを取得しようとする
    with pytest.raises(StatementError) as exc_info:
        # 無効なUUID文字列を直接クエリに渡す
        await user.get_by_id(db_session, invalid_id)
    
    # エラーメッセージを検証
    error_message = str(exc_info.value)
    assert "invalid uuid" in error_message.lower()
