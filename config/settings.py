"""
Complete configuration for the Advanced Cryptocurrency Trading Signal Bot.
All settings, API keys, trading parameters, and indicator configurations.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

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

    # ── Telegram ───────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'trading_bot.db'}")

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
    CANDLE_LIMIT: int = 200

    # ── Multi-Timeframe Analysis ──────────────────────────────────────
    MTF_TIMEFRAMES: list = ["5m", "1h", "4h"]
    MTF_CANDLE_LIMITS: dict = {"5m": 200, "1h": 200, "4h": 200}

    # ── Binary Trading ────────────────────────────────────────────────
    BINARY_ENABLED: bool = True
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
    ML_TRAINING_CANDLES: int = 500
    ML_PREDICTION_HORIZON: int = 5

    # ── Technical Indicator Settings ───────────────────────────────────
    INDICATORS = {
        "rsi": {"period": 14, "overbought": 70, "oversold": 30},
        "ema": {"fast": 20, "medium": 50, "slow": 200},
        "macd": {"fast": 12, "slow": 26, "signal": 9},
        "bollinger_bands": {"period": 20, "std_dev": 2.0},
        "atr": {"period": 14},
        "adx": {"period": 14, "strong_trend": 25},
    }

    # ── Signal Thresholds ──────────────────────────────────────────────
    MIN_SIGNAL_CONFIDENCE: float = 0.6  # 60% minimum confidence
    MIN_INDICATORS_AGREE: int = 2  # At least 2 out of 3 must agree

    # ── Risk Management ────────────────────────────────────────────────
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
    BACKTEST_START_DATE: str = "2024-01-01"
    BACKTEST_END_DATE: str = "2024-12-31"
    BACKTEST_INITIAL_CAPITAL: float = 10000.0
    BACKTEST_COMMISSION: float = 0.001  # 0.1%

    # ── Bot Loop ───────────────────────────────────────────────────────
    SCAN_INTERVAL_SECONDS: int = 300  # 5 minutes

    # ── Logging ────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE: str = "trading_bot.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5