import logging
import sys

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# アプリケーション全体で使用するロガー
app_logger = logging.getLogger("post-service")
