# User CRUD テスト仕様書

## テストファイル構成

テストは以下の 3 つのファイルに分かれています：

- `test_user_normal.py`: 正常系テスト
- `test_user_error.py`: 異常系テスト
- `test_user_boundary.py`: 境界値テスト

## テストケース一覧

### 正常系テスト (`test_user_normal.py`)

| テスト関数                         | テスト内容                   | 主なアサーション                                                                                |
| ---------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------- |
| `test_create_user`                 | ユーザー作成の基本機能       | - ID が生成されていること<br>- ユーザー名が正しいこと<br>- パスワードがハッシュ化されていること |
| `test_get_user_by_id_exists`       | ID によるユーザー取得        | - ユーザーが取得できること<br>- 取得したユーザーの情報が正しいこと                              |
| `test_get_user_by_username_exists` | ユーザー名によるユーザー取得 | - ユーザーが取得できること<br>- 取得したユーザーの情報が正しいこと                              |
| `test_update_username`             | ユーザー名の更新             | - 更新後のユーザー名が正しいこと<br>- DB に反映されていること                                   |
| `test_update_password`             | パスワードの更新             | - 新しいパスワードで認証できること<br>- 古いパスワードで認証できないこと                        |
| `test_delete_user`                 | ユーザーの削除               | - ユーザーが削除されていること<br>- 削除後に取得できないこと                                    |

### 異常系テスト (`test_user_error.py`)

| テスト関数                                | テスト内容                              | 期待される例外/結果 |
| ----------------------------------------- | --------------------------------------- | ------------------- |
| `test_create_user_with_empty_username`    | 空のユーザー名でのユーザー作成          | ValidationError     |
| `test_create_user_with_too_long_username` | 51 文字以上のユーザー名でのユーザー作成 | ValidationError     |
| `test_create_user_with_empty_password`    | 空のパスワードでのユーザー作成          | ValidationError     |
| `test_create_user_with_too_long_password` | 17 文字以上のパスワードでのユーザー作成 | ValidationError     |
| `test_create_duplicate_username`          | 重複するユーザー名でのユーザー作成      | IntegrityError      |
| `test_get_user_by_invalid_id`             | 無効な UUID でのユーザー取得            | StatementError      |
| `test_get_user_by_nonexistent_id`         | 存在しない ID でのユーザー取得          | None                |
| `test_get_user_by_nonexistent_username`   | 存在しないユーザー名でのユーザー取得    | None                |
| `test_update_user_with_too_long_username` | 51 文字以上のユーザー名への更新         | ValidationError     |
| `test_update_user_with_too_long_password` | 17 文字以上のパスワードへの更新         | ValidationError     |
| `test_update_to_duplicate_username`       | 重複するユーザー名への更新              | IntegrityError      |
| `test_update_nonexistent_user`            | 存在しないユーザーの更新                | Exception           |
| `test_delete_nonexistent_user`            | 存在しないユーザーの削除                | Exception           |

### 境界値テスト (`test_user_boundary.py`)

| テスト関数                                             | テスト内容                   | 検証項目                                                           |
| ------------------------------------------------------ | ---------------------------- | ------------------------------------------------------------------ |
| `test_create_user_with_minimum_length_username`        | 1 文字のユーザー名           | - ユーザーが作成できること<br>- 正しく保存されること               |
| `test_create_user_with_maximum_length_username`        | 50 文字のユーザー名          | - ユーザーが作成できること<br>- 正しく保存されること               |
| `test_create_user_with_minimum_length_password`        | 1 文字のパスワード           | - ユーザーが作成できること<br>- パスワード認証が機能すること       |
| `test_create_user_with_maximum_length_password`        | 16 文字のパスワード          | - ユーザーが作成できること<br>- パスワード認証が機能すること       |
| `test_create_user_with_special_characters_in_username` | 特殊文字を含むユーザー名     | - ユーザーが作成できること<br>- 特殊文字が正しく保存されること     |
| `test_create_user_with_unicode_characters_in_username` | Unicode 文字を含むユーザー名 | - ユーザーが作成できること<br>- Unicode 文字が正しく保存されること |

## 検証項目の詳細

### データベースの整合性

- 各操作後にデータベースの状態が期待通りであること
- トランザクションが適切に処理されること
- エラー時にロールバックが機能すること

### セキュリティ

- パスワードが適切にハッシュ化されていること
- 元のパスワードがデータベースに保存されていないこと
- パスワード認証が正しく機能すること

### バリデーション

- 入力値の長さ制限が守られていること
- 必須フィールドのチェックが機能していること
- ユニーク制約が守られていること

### エラーハンドリング

- 適切な例外が発生すること
- エラーメッセージが明確であること
- エラー時にデータベースの整合性が保たれること
