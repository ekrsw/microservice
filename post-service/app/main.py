from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.init import init_db
from app.core.logging import app_logger as logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS設定
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# APIルーターの登録
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """
    アプリケーション起動時の処理
    """
    logger.info("Starting up Post Service...")
    
    # データベースの初期化
    await init_db()
    
    logger.info("Post Service started successfully")

@app.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return {"status": "ok"}

@app.get("/")
async def root():
    """
    ルートエンドポイント
    """
    return {
        "message": "Welcome to Post Service API",
        "docs": f"{settings.API_V1_STR}/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
