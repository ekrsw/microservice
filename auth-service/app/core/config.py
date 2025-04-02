from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # データベース設定
    DATABASE_URL: str = "sqlite+aiosqlite:///test.db"
    SQLALCHEMY_ECHO: bool = False  # SQLAlchemyのログ出力設定を追加

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="",
    )

settings = Settings()