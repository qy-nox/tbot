"""
Complete configuration for the Advanced Cryptocurrency Trading Signal Bot.
All settings, API keys, trading parameters, and indicator configurations.
"""

import os
import re
import warnings
from pathlib import Path

try:
    from dotenv import load_dotenv as _load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional for bare runtime/tests
    def _no_op_load_dotenv(*args, **kwargs):
        warnings.warn(
            "python-dotenv is not installed; .env file loading is disabled.",
            RuntimeWarning,
            stacklevel=2,
        )
        return False

    _load_dotenv = _no_op_load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = BASE_DIR / ".env"

# Load environment variables from .env file (force repository .env path)
_load_dotenv(dotenv_path=_ENV_FILE, override=False)


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        warnings.warn(
            f"Invalid integer for {key}={raw!r}; using fallback {default}.",
            RuntimeWarning,
            stacklevel=2,
        )
        return default


def is_valid_telegram_token(token: str | None) -> bool:
    """Return True when token follows Telegram '<id>:<secret>' shape."""
    return bool(token and ":" in token and len(token.split(":", 1)[1]) >= 8)


def is_valid_telegram_chat_id(chat_id: str | None) -> bool:
    """Return True when chat_id looks like a Telegram numeric id/channel id."""
    if chat_id is None:
        return False
    value = str(chat_id).strip()
    return bool(re.fullmatch(r"-?\d+", value))


PLACEHOLDER_TELEGRAM_GROUP_IDS = {
    "-1001234567890",
    "-1001234567891",
}


def is_placeholder_telegram_group_id(chat_id: str | None) -> bool:
    """Return True when chat_id is a documented placeholder example."""
    if chat_id is None:
        return False
    return str(chat_id).strip() in PLACEHOLDER_TELEGRAM_GROUP_IDS


def parse_telegram_channels(raw: str | None) -> list[str]:
    """Parse comma-separated chat/channel ids and keep only valid values."""
    channels: list[str] = []
    if not raw:
        return channels
    for item in str(raw).split(","):
        value = item.strip()
        if is_valid_telegram_chat_id(value):
            channels.append(value)
    return channels


class Settings:
    """Centralized configuration manager."""

    # ── Exchange API Keys ──────────────────────────────────────────────
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")
    EXCHANGE_ID: str = os.getenv("EXCHANGE_ID", "binance")

    # ── Finnhub API Key (news) ─────────────────────────────────────────
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")

    # ── Telegram ───────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_TOKEN_MAIN: str = TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN_MAIN", "")
    TELEGRAM_BOT_TOKEN_SUB: str = (
        os.getenv("BOT1_SUBSCRIPTION_TOKEN")
        or os.getenv("TELEGRAM_BOT_TOKEN_SUB")
        or os.getenv("TELEGRAM_TOKEN_BOT1", "")
    )
    TELEGRAM_BOT_TOKEN_ADMIN: str = (
        os.getenv("BOT2_ADMIN_TOKEN")
        or os.getenv("TELEGRAM_BOT_TOKEN_ADMIN")
        or os.getenv("TELEGRAM_TOKEN_BOT2", "")
    )
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    TELEGRAM_BROADCAST_CHANNELS: list[str] = parse_telegram_channels(
        os.getenv("BROADCAST_TELEGRAM_CHANNELS", "")
    )
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = _env_int("SMTP_PORT", 587)
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")


    # ── Telegram Ecosystem (3-bot deployment) ──────────────────────────
    TELEGRAM_BOT_TOKEN_MAIN_SIGNAL: str = os.getenv("TELEGRAM_BOT_TOKEN_MAIN_SIGNAL", TELEGRAM_BOT_TOKEN_MAIN)
    TELEGRAM_BOT_TOKEN_SUBSCRIPTION: str = os.getenv("TELEGRAM_BOT_TOKEN_SUBSCRIPTION", TELEGRAM_BOT_TOKEN_SUB)
    TELEGRAM_BOT_TOKEN_ADMIN_ECOSYSTEM: str = os.getenv("TELEGRAM_BOT_TOKEN_ADMIN_ECOSYSTEM", TELEGRAM_BOT_TOKEN_ADMIN)

    # ── Payment Integrations ────────────────────────────────────────────
    BINANCE_P2P_API_KEY: str = os.getenv("BINANCE_P2P_API_KEY", "")
    BINANCE_P2P_API_SECRET: str = os.getenv("BINANCE_P2P_API_SECRET", "")
    BKASH_APP_KEY: str = os.getenv("BKASH_APP_KEY", "")
    BKASH_APP_SECRET: str = os.getenv("BKASH_APP_SECRET", "")
    BKASH_USERNAME: str = os.getenv("BKASH_USERNAME", "")
    BKASH_PASSWORD: str = os.getenv("BKASH_PASSWORD", "")
    MANUAL_BANK_ACCOUNT_NAME: str = os.getenv("MANUAL_BANK_ACCOUNT_NAME", "")
    MANUAL_BANK_ACCOUNT_NUMBER: str = os.getenv("MANUAL_BANK_ACCOUNT_NUMBER", "")
    MANUAL_BANK_ROUTING: str = os.getenv("MANUAL_BANK_ROUTING", "")

    # ── Managed Group IDs (12 groups) ───────────────────────────────────
    SIGNAL_GROUP_IDS: list[str] = [
        os.getenv("SIGNAL_GROUP_1_ID", ""),
        os.getenv("SIGNAL_GROUP_2_ID", ""),
        os.getenv("SIGNAL_GROUP_3_ID", ""),
        os.getenv("SIGNAL_GROUP_4_ID", ""),
        os.getenv("SIGNAL_GROUP_5_ID", ""),
        os.getenv("SIGNAL_GROUP_6_ID", ""),
        os.getenv("SIGNAL_GROUP_7_ID", ""),
        os.getenv("SIGNAL_GROUP_8_ID", ""),
        os.getenv("SIGNAL_GROUP_9_ID", ""),
        os.getenv("SIGNAL_GROUP_10_ID", ""),
        os.getenv("SIGNAL_GROUP_11_ID", ""),
        os.getenv("SIGNAL_GROUP_12_ID", ""),
    ]
    SIGNAL_GROUP_LABELS: tuple[str, ...] = (
        "Crypto B Grade High Volume",
        "Crypto B Grade VIP",
        "Crypto A Grade High Volume",
        "Crypto A Grade VIP",
        "Crypto A+ Grade High Volume",
        "Crypto A+ Grade VIP",
        "Binary B Grade High Volume",
        "Binary B Grade VIP",
        "Binary A Grade High Volume",
        "Binary A Grade VIP",
        "Binary A+ Grade High Volume",
        "Binary A+ Grade VIP",
    )

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'trading_bot.db'}")
    DB_POOL_SIZE: int = _env_int("DB_POOL_SIZE", 5)
    DB_MAX_OVERFLOW: int = _env_int("DB_MAX_OVERFLOW", 10)

    # ── Trading Mode ───────────────────────────────────────────────────
    TRADING_MODE: str = os.getenv("TRADING_MODE", "paper")  # paper | live

    # ── Trading Pairs ──────────────────────────────────────────────────
    TRADING_PAIRS: list = [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "SOL/USDT",
        "XRP/USDT",
        "ADA/USDT",
    ]

    # ── Timeframes ─────────────────────────────────────────────────────
    TIMEFRAME: str = "1h"
    TIMEFRAMES: list = ["5m", "15m", "1h", "4h", "1d"]
    CANDLE_LIMIT: int = 200

    # ── Multi-Timeframe Analysis ──────────────────────────────────────
    MTF_TIMEFRAMES: list = ["5m", "1h", "4h"]
    MTF_CANDLE_LIMITS: dict = {"5m": 200, "1h": 200, "4h": 200}

    # ── Binary Trading ────────────────────────────────────────────────
    BINARY_ENABLED: bool = True
    IQ_OPTION_EMAIL: str = os.getenv("IQ_OPTION_EMAIL", "")
    IQ_OPTION_PASSWORD: str = os.getenv("IQ_OPTION_PASSWORD", "")
    POCKET_OPTION_TOKEN: str = os.getenv("POCKET_OPTION_TOKEN", "")
    BINARY_PAIRS: list = [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "SOL/USDT",
        "XRP/USDT",
    ]
    BINARY_TIMEFRAME: str = "5m"
    BINARY_EXPIRY_SECONDS: int = 300  # 5 minutes
    BINARY_MIN_CONFIDENCE: float = 0.70

    # ── ML Engine ─────────────────────────────────────────────────────
    ML_ENABLED: bool = True
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "models/")
    LSTM_ENABLED: bool = os.getenv("LSTM_ENABLED", "true").lower() == "true"
    XGBOOST_ENABLED: bool = os.getenv("XGBOOST_ENABLED", "true").lower() == "true"
    ML_TRAINING_CANDLES: int = 500
    ML_PREDICTION_HORIZON: int = 5
    SENTIMENT_ENABLED: bool = os.getenv("SENTIMENT_ENABLED", "true").lower() == "true"
    VADER_ENABLED: bool = os.getenv("VADER_ENABLED", "true").lower() == "true"
    TEXTBLOB_ENABLED: bool = os.getenv("TEXTBLOB_ENABLED", "true").lower() == "true"

    # ── Technical Indicator Settings ───────────────────────────────────
    INDICATORS = {
        "rsi": {"period": 14, "overbought": 70, "oversold": 30},
        "ema": {"fast": 20, "medium": 50, "slow": 200},
        "macd": {"fast": 12, "slow": 26, "signal": 9},
        "bollinger_bands": {"period": 20, "std_dev": 2.0},
        "atr": {"period": 14},
        "adx": {"period": 14, "strong_trend": 25},
    }
    RSI_PERIOD: int = int(os.getenv("RSI_PERIOD", "14"))
    RSI_OVERSOLD: int = int(os.getenv("RSI_OVERSOLD", "30"))
    RSI_OVERBOUGHT: int = int(os.getenv("RSI_OVERBOUGHT", "70"))
    EMA_PERIODS: list = [20, 50, 200]
    ATR_PERIOD: int = int(os.getenv("ATR_PERIOD", "14"))

    # ── Signal Thresholds ──────────────────────────────────────────────
    MIN_SIGNAL_CONFIDENCE: float = 0.6  # 60% minimum confidence
    MIN_INDICATORS_AGREE: int = 2  # At least 2 out of 3 must agree

    # ── Risk Management ────────────────────────────────────────────────
    MAX_TRADES_PER_DAY: int = int(os.getenv("MAX_TRADES_PER_DAY", "5"))
    MAX_POSITIONS: int = int(os.getenv("MAX_POSITIONS", "3"))
    RISK_PER_TRADE: float = 0.02  # 2% of portfolio per trade
    MAX_OPEN_TRADES: int = 5
    MAX_DRAWDOWN: float = 0.10  # 10% max drawdown
    RISK_REWARD_RATIO: float = 2.0  # 1:2 minimum
    STOP_LOSS_ATR_MULTIPLIER: float = 1.5
    TAKE_PROFIT_LEVELS: list = [1.0, 1.5, 2.0]  # TP1, TP2, TP3 as ATR multiples

    # ── Portfolio ──────────────────────────────────────────────────────
    INITIAL_CAPITAL: float = 10000.0  # USD

    # ── Filters ────────────────────────────────────────────────────────
    FILTERS = {
        "trend_filter": True,
        "momentum_filter": True,
        "volatility_filter": True,
        "adx_filter": True,
        "news_filter": True,
        "min_adx": 20,
        "max_volatility_pct": 5.0,
    }

    # ── Backtesting ────────────────────────────────────────────────────
    BACKTEST_ENABLED: bool = os.getenv("BACKTEST_ENABLED", "true").lower() == "true"
    BACKTEST_DAYS: int = int(os.getenv("BACKTEST_DAYS", "252"))
    MIN_CONFIRMATIONS: int = int(os.getenv("MIN_CONFIRMATIONS", "3"))
    BACKTEST_START_DATE: str = "2024-01-01"
    BACKTEST_END_DATE: str = "2024-12-31"
    BACKTEST_INITIAL_CAPITAL: float = 10000.0
    BACKTEST_COMMISSION: float = 0.001  # 0.1%

    # ── Bot Loop ───────────────────────────────────────────────────────
    SCAN_INTERVAL_SECONDS: int = 300  # 5 minutes
    EXCHANGE_RETRY_ATTEMPTS: int = int(os.getenv("EXCHANGE_RETRY_ATTEMPTS", "3"))
    EXCHANGE_RETRY_BACKOFF_SECONDS: float = float(os.getenv("EXCHANGE_RETRY_BACKOFF_SECONDS", "1.0"))
    OHLCV_CACHE_TTL_SECONDS: int = int(os.getenv("OHLCV_CACHE_TTL_SECONDS", "30"))
    OHLCV_CACHE_MAX_ENTRIES: int = int(os.getenv("OHLCV_CACHE_MAX_ENTRIES", "256"))
    CALENDAR_ENABLED: bool = os.getenv("CALENDAR_ENABLED", "true").lower() == "true"
    HIGH_IMPACT_SKIP_MINUTES: int = int(os.getenv("HIGH_IMPACT_SKIP_MINUTES", "30"))

    # ── Security ───────────────────────────────────────────────────────
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    MODEL_SIGNING_KEY: str = os.getenv("MODEL_SIGNING_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    API_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "120"))
    ML_MODEL_MAX_IDLE_SECONDS: int = int(os.getenv("ML_MODEL_MAX_IDLE_SECONDS", "1800"))
    ADMIN_DASHBOARD_REQUIRE_AUTH: bool = os.getenv("ADMIN_DASHBOARD_REQUIRE_AUTH", "false").lower() == "true"
    SIGNAL_DEDUP_WINDOW_MINUTES: int = int(os.getenv("SIGNAL_DEDUP_WINDOW_MINUTES", "5"))

    # ── Logging ────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE: str = "trading_bot.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    TELEGRAM_RETRY_ATTEMPTS: int = _env_int("TELEGRAM_RETRY_ATTEMPTS", 3)

    @classmethod
    def configured_signal_group_ids(cls) -> list[str]:
        return [str(value).strip() for value in cls.SIGNAL_GROUP_IDS if str(value).strip()]

    @classmethod
    def invalid_signal_group_ids(cls) -> list[str]:
        invalid: list[str] = []
        for value in cls.configured_signal_group_ids():
            if not is_valid_telegram_chat_id(value) or is_placeholder_telegram_group_id(value):
                invalid.append(value)
        return invalid

    @classmethod
    def valid_signal_group_ids(cls) -> list[str]:
        valid: list[str] = []
        for value in cls.configured_signal_group_ids():
            if value in valid:
                continue
            if is_valid_telegram_chat_id(value) and not is_placeholder_telegram_group_id(value):
                valid.append(value)
        return valid

    @classmethod
    def validate_startup_config(cls) -> list[str]:
        """Return configuration errors that should block optional integrations."""
        errors: list[str] = []
        if cls.TELEGRAM_BOT_TOKEN and not is_valid_telegram_token(cls.TELEGRAM_BOT_TOKEN):
            errors.append("TELEGRAM_BOT_TOKEN format is invalid (expected '<id>:<token>').")
        if cls.TELEGRAM_CHAT_ID and not is_valid_telegram_chat_id(cls.TELEGRAM_CHAT_ID):
            errors.append("TELEGRAM_CHAT_ID must be numeric (example: 123456789 or -1001234567890).")
        if cls.TELEGRAM_BOT_TOKEN and not (
            is_valid_telegram_chat_id(cls.TELEGRAM_CHAT_ID) or cls.TELEGRAM_BROADCAST_CHANNELS
        ):
            errors.append("Telegram enabled but no valid TELEGRAM_CHAT_ID or BROADCAST_TELEGRAM_CHANNELS set.")
        invalid_groups = cls.invalid_signal_group_ids()
        if invalid_groups:
            errors.append(
                "Invalid SIGNAL_GROUP_*_ID entries detected: "
                + ", ".join(invalid_groups)
                + ". Use real Telegram group IDs and run scripts/setup_groups_wizard.py."
            )
        if cls.TELEGRAM_BOT_TOKEN and cls.configured_signal_group_ids() and not cls.valid_signal_group_ids():
            errors.append("All configured SIGNAL_GROUP_*_ID entries are invalid; group distribution is disabled.")
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL is missing.")
        return errors

    @classmethod
    def startup_snapshot(cls) -> dict[str, object]:
        """Return non-sensitive startup configuration values for diagnostics."""
        return {
            "database_url": cls.DATABASE_URL,
            "exchange_id": cls.EXCHANGE_ID,
            "api_rate_limit_per_minute": cls.API_RATE_LIMIT_PER_MINUTE,
            "scan_interval_seconds": cls.SCAN_INTERVAL_SECONDS,
            "telegram_enabled": bool(
                cls.TELEGRAM_BOT_TOKEN
                and (is_valid_telegram_chat_id(cls.TELEGRAM_CHAT_ID) or cls.TELEGRAM_BROADCAST_CHANNELS)
            ),
            "telegram_primary_chat_id": cls.TELEGRAM_CHAT_ID or None,
            "telegram_broadcast_channels": cls.TELEGRAM_BROADCAST_CHANNELS,
            "signal_group_ids_configured": len(cls.configured_signal_group_ids()),
            "signal_group_ids_valid": len(cls.valid_signal_group_ids()),
            "signal_group_ids_invalid": cls.invalid_signal_group_ids(),
            "finnhub_enabled": bool(cls.FINNHUB_API_KEY),
        }
