"""
Complete configuration for the Advanced Cryptocurrency Trading Signal Bot.
All settings, API keys, trading parameters, and indicator configurations.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional for bare runtime/tests
    def load_dotenv(*_args, **_kwargs):  # type: ignore[no-redef]
        return False

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


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
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'trading_bot.db'}")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # ── Trading Mode ───────────────────────────────────────────────────
    TRADING_MODE: str = os.getenv("TRADING_MODE", "paper")  # paper | live

    # ── Trading Pairs ──────────────────────────────────────────────────
    TRADING_PAIRS: list = [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
        "SOL/USDT",
        "ADA/USDT",
        "XRP/USDT",
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
