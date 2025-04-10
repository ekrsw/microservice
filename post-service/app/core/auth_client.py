import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logging import app_logger as logger

class AuthClient:
    """
    auth-serviceと通信するためのクライアントクラス
    """
    def __init__(self):
        # auth-serviceのベースURL
        self.base_url = "http://auth-service:8080/api/v1/auth"
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        auth-serviceのログインエンドポイントを呼び出す
        
        Args:
            username: ユーザー名
            password: パスワード
            
        Returns:
            Dict[str, Any]: アクセストークンとリフレッシュトークンを含むレスポンス
            
        Raises:
            HTTPException: 認証に失敗した場合
        """
        try:
            # auth-serviceのログインエンドポイントにリクエスト
            response = await self.client.post(
                f"{self.base_url}/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # レスポンスのステータスコードを確認
            if response.status_code == 200:
                return response.json()
            else:
                # エラーレスポンスの詳細を取得
                error_detail = "認証に失敗しました"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_detail = error_data["detail"]
                except:
                    pass
                
                logger.error(f"auth-serviceへのログイン失敗: {error_detail}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_detail,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except httpx.RequestError as e:
            logger.error(f"auth-serviceへの接続エラー: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="認証サービスに接続できません",
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        リフレッシュトークンを使用して新しいアクセストークンを取得
        
        Args:
            refresh_token: リフレッシュトークン
            
        Returns:
            Dict[str, Any]: 新しいアクセストークンとリフレッシュトークンを含むレスポンス
            
        Raises:
            HTTPException: トークンの更新に失敗した場合
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/refresh",
                json={"refresh_token": refresh_token}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = "トークンの更新に失敗しました"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_detail = error_data["detail"]
                except:
                    pass
                
                logger.error(f"auth-serviceでのトークン更新失敗: {error_detail}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_detail,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except httpx.RequestError as e:
            logger.error(f"auth-serviceへの接続エラー: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="認証サービスに接続できません",
            )
    
    async def logout(self, refresh_token: str) -> Dict[str, Any]:
        """
        ログアウトしてリフレッシュトークンを無効化
        
        Args:
            refresh_token: リフレッシュトークン
            
        Returns:
            Dict[str, Any]: ログアウト結果を含むレスポンス
            
        Raises:
            HTTPException: ログアウトに失敗した場合
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/logout",
                json={"refresh_token": refresh_token}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = "ログアウトに失敗しました"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_detail = error_data["detail"]
                except:
                    pass
                
                logger.error(f"auth-serviceでのログアウト失敗: {error_detail}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_detail,
                )
        except httpx.RequestError as e:
            logger.error(f"auth-serviceへの接続エラー: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="認証サービスに接続できません",
            )
    
    async def close(self):
        """
        HTTPクライアントを閉じる
        """
        await self.client.aclose()

# シングルトンインスタンス
auth_client = AuthClient()
