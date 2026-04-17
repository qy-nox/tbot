"""
Logging configuration for the trading bot.
Provides rotating file and console handlers with colored output.
"""

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import Settings
from core.security import redact_sensitive


def _mask_sensitive_values(message: str) -> str:
    masked = redact_sensitive(message)
    masked = re.sub(
        r"(?i)\b([a-z0-9_-]*(?:api[_-]?key|secret|token|password|passphrase)[a-z0-9_-]*)\b\s*=\s*([^\s,;]+)",
        r"\1=***",
        masked,
    )
    sensitive_values = (
        Settings.BINANCE_API_KEY,
        Settings.BINANCE_API_SECRET,
        Settings.TELEGRAM_BOT_TOKEN,
        Settings.TELEGRAM_BOT_TOKEN_MAIN,
        Settings.TELEGRAM_BOT_TOKEN_SUB,
        Settings.TELEGRAM_BOT_TOKEN_ADMIN,
        Settings.FINNHUB_API_KEY,
    )
    for value in sensitive_values:
        if value:
            masked = masked.replace(value, "***")
    return masked


class _SensitiveDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        record.msg = _mask_sensitive_values(message)
        record.args = ()
        return True


def setup_logger(name: str = "trading_bot") -> logging.Logger:
    """Create and configure a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_SensitiveDataFilter())
    logger.addHandler(console_handler)

    # File handler (rotating)
    log_dir = Path(Settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / Settings.LOG_FILE,
        maxBytes=Settings.LOG_MAX_BYTES,
        backupCount=Settings.LOG_BACKUP_COUNT,
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_SensitiveDataFilter())
    logger.addHandler(file_handler)

    return logger
