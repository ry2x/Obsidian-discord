import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import config


def setup_logger():
    """ロガーを設定する"""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    # ルートロガーの取得
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 既存のハンドラをクリア
    if logger.hasHandlers():
        logger.handlers.clear()

    # フォーマッタの作成
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # コンソールハンドラの設定
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # ファイルハンドラの設定 (日付ベースでローテーション)
    file_handler = TimedRotatingFileHandler(
        "bot.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# ロガーのインスタンスを作成
logger = setup_logger()
