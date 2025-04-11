# 異常系テスト
import pytest
from pydantic import ValidationError
import uuid
from app.core.security import verify_password
from app.crud.user import user
from app.schemas.user import PasswordUpdate, UserCreate, UserUpdate
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
    db_obj = await user.create(db_session, first_user)
    
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

    # テストの検証は完了したので、ここでテストを終了する
    # フィクスチャがロールバックするため、明示的なクリーンアップは不要

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

@pytest.mark.asyncio
async def test_get_user_by_nonexistent_id(db_session):
    # 存在しないが有効なUUID形式のIDを生成
    nonexistent_id = uuid.uuid4()
    
    # 存在しないIDでユーザーを取得
    result = await user.get_by_id(db_session, nonexistent_id)
    
    # 結果がNoneであることを確認
    assert result is None

    # データベースに影響がないことを確認
    users = await db_session.execute(select(User))
    users_list = users.scalars().all()
    initial_count = len(users_list)
    
    # 再度同じIDで取得を試みる
    result = await user.get_by_id(db_session, nonexistent_id)
    assert result is None
    
    # データベースのユーザー数が変わっていないことを確認
    users = await db_session.execute(select(User))
    users_list = users.scalars().all()
    assert len(users_list) == initial_count

@pytest.mark.asyncio
async def test_get_user_by_nonexistent_username(db_session):
    # 存在しないユーザー名
    nonexistent_username = "nonexistentuser123"
    
    # 存在しないユーザー名でユーザーを取得
    result = await user.get_by_username(db_session, nonexistent_username)
    
    # 結果がNoneであることを確認
    assert result is None

    # データベースに影響がないことを確認
    users = await db_session.execute(select(User))
    users_list = users.scalars().all()
    initial_count = len(users_list)
    
    # 再度同じユーザー名で取得を試みる
    result = await user.get_by_username(db_session, nonexistent_username)
    assert result is None
    
    # データベースのユーザー数が変わっていないことを確認
    users = await db_session.execute(select(User))
    users_list = users.scalars().all()
    assert len(users_list) == initial_count

    # 特殊文字を含むユーザー名でも試してみる
    special_username = "user@123!#$"
    result = await user.get_by_username(db_session, special_username)
    assert result is None

# Update操作テスト
# バリデーションエラー
@pytest.mark.asyncio
async def test_update_user_with_too_long_username(db_session):
    # 既存のユーザーを作成
    user_in = UserCreate(
        username="originaluser",
        password="password123"
    )
    db_user = await user.create(db_session, user_in)
    
    # 51文字のユーザー名を生成（最大制限は50文字）
    too_long_username = "a" * 51
    
    # 長すぎるユーザー名でUserUpdateスキーマを作成しようとする
    with pytest.raises(ValidationError) as exc_info:
        user_update = UserUpdate(username=too_long_username)
    
    # エラーの詳細を検証
    error = exc_info.value.errors()
    assert len(error) == 1
    assert error[0]["type"] == "string_too_long"
    assert error[0]["loc"] == ("username",)
    assert error[0]["ctx"]["max_length"] == 50

    # データベースのユーザー名が変更されていないことを確認
    db_user_check = await user.get_by_id(db_session, db_user.id)
    assert db_user_check.username == "originaluser"

    # テストの検証は完了したので、ここでテストを終了する
    # フィクスチャがロールバックするため、明示的なクリーンアップは不要

@pytest.mark.asyncio
async def test_update_user_with_too_long_password(db_session):
    # 既存のユーザーを作成
    user_in = UserCreate(
        username="testuser",
        password="originalpass123"
    )
    db_user = await user.create(db_session, user_in)
    
    # 17文字のパスワードを生成（最大制限は16文字）
    too_long_password = "a" * 17
    
    # 長すぎるパスワードでPasswordUpdateスキーマを作成しようとする
    with pytest.raises(ValidationError) as exc_info:
        password_update = PasswordUpdate(
            current_password="originalpass123",
            new_password=too_long_password
        )
    
    # エラーの詳細を検証
    error = exc_info.value.errors()
    assert len(error) == 1
    assert error[0]["type"] == "string_too_long"
    assert error[0]["loc"] == ("new_password",)
    assert error[0]["ctx"]["max_length"] == 16

    # データベースのパスワードが変更されていないことを確認
    db_user_check = await user.get_by_id(db_session, db_user.id)
    assert verify_password("originalpass123", db_user_check.hashed_password)

    # テストの検証は完了したので、ここでテストを終了する
    # フィクスチャがロールバックするため、明示的なクリーンアップは不要

@pytest.mark.asyncio
async def test_update_to_duplicate_username(db_session):
    # 2人のユーザーを作成
    first_user = UserCreate(
        username="firstuser",
        password="password123"
    )
    second_user = UserCreate(
        username="seconduser",
        password="password123"
    )
    db_first_user = await user.create(db_session, first_user)
    db_second_user = await user.create(db_session, second_user)

    # 2人目のユーザーのユーザー名を1人目と同じものに更新しようとする
    user_update = UserUpdate(username="firstuser")
    
    # IntegrityErrorが発生することを確認
    with pytest.raises(IntegrityError) as exc_info:
        await user.update(db_session, db_second_user, user_update)
    
    # エラーメッセージにユニーク制約違反が含まれていることを確認
    assert "unique constraint" in str(exc_info.value).lower()
    
    # テストの検証は完了したので、ここでテストを終了する
    # フィクスチャがロールバックするため、明示的なクリーンアップは不要

@pytest.mark.asyncio
async def test_update_nonexistent_user(db_session):
    # 存在しないユーザーを表すダミーユーザーオブジェクトを作成
    from app.models.user import User
    from uuid import uuid4
    
    nonexistent_user = User(
        id=uuid4(),
        username="nonexistent",
        hashed_password="dummy"
    )
    
    # 存在しないユーザーの更新を試みる
    user_update = UserUpdate(username="newname")
    
    # SQLAlchemyのエラーが発生することを確認
    with pytest.raises(Exception) as exc_info:  # 具体的な例外型はSQLAlchemyの実装に依存
        await user.update(db_session, nonexistent_user, user_update)
    
    # エラーメッセージを確認（SQLAlchemyの実際のエラーメッセージに合わせる）
    error_message = str(exc_info.value)
    assert "not persistent within this session" in error_message.lower()
    
    # データベースに影響がないことを確認
    result = await user.get_by_username(db_session, "newname")
    assert result is None

# Delete操作テスト
@pytest.mark.asyncio
async def test_delete_nonexistent_user(db_session):
    # 存在しないユーザーを表すダミーユーザーオブジェクトを作成
    nonexistent_user = User(
        id=uuid.uuid4(),
        username="nonexistent",
        hashed_password="dummy"
    )
    
    # データベースの初期状態を記録
    users = await db_session.execute(select(User))
    initial_users = users.scalars().all()
    initial_count = len(initial_users)
    
    # 存在しないユーザーの削除を試みる
    with pytest.raises(Exception) as exc_info:  # 具体的な例外型はSQLAlchemyの実装に依存
        await user.delete(db_session, nonexistent_user)
    
    # エラーメッセージを確認
    error_message = str(exc_info.value)
    assert "not found" in error_message.lower() or "no row was found" in error_message.lower()
    
    # データベースの状態が変更されていないことを確認
    users = await db_session.execute(select(User))
    current_users = users.scalars().all()
    assert len(current_users) == initial_count
    
    # 各ユーザーが維持されていることを確認
    for initial_user, current_user in zip(initial_users, current_users):
        assert initial_user.id == current_user.id
        assert initial_user.username == current_user.username
