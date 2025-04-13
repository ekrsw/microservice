from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, Literal
import os
from pathlib import Path

class Settings(BaseSettings):
    # プロジェクト設定
    PROJECT_NAME: str = "Post Service"
    API_V1_STR: str = "/api/v1"
    
    # 環境設定
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    
    # ロギング設定
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: str = "logs/post_service.log"
    
    # データベース設定
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    
    # テスト用データベース設定
    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str
    TEST_POSTGRES_HOST: str
    TEST_POSTGRES_PORT: str
    TEST_POSTGRES_DB: str
    
    # CORS設定
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # JWT設定
    ALGORITHM: str = "RS256"
    
    # 公開鍵のパス
    PUBLIC_KEY_PATH: str = "keys/public.pem"
    
    # APIのホストとポート
    API_HOST: str = "0.0.0.0"
    POST_SERVICE_INTERNAL_PORT: int = 8081
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # テスト用データベースURL
    @property
    def TEST_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.TEST_POSTGRES_USER}:{self.TEST_POSTGRES_PASSWORD}@{self.TEST_POSTGRES_HOST}:5432/{self.TEST_POSTGRES_DB}"
    
    SQLALCHEMY_ECHO: bool = False
    
    @property
    def PUBLIC_KEY(self) -> str:
        """公開鍵の内容を読み込む"""
        try:
            with open(self.PUBLIC_KEY_PATH, "r") as f:
                return f.read()
        except FileNotFoundError:
            print(f"警告: 公開鍵ファイルが見つかりません: {self.PUBLIC_KEY_PATH}")
            return os.environ.get("PUBLIC_KEY", "")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="",
    )

settings = Settings()
