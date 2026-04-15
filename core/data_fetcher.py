"""
Data fetching module for the trading bot.
Retrieves OHLCV data, crypto news, economic calendar events,
funding rates, and volume profiles from various sources.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import ccxt
import numpy as np
import pandas as pd
import requests

from config.settings import Settings

logger = logging.getLogger("trading_bot.data_fetcher")


class DataFetcher:
    """Fetches market data from exchanges and external APIs."""

    def __init__(self) -> None:
        self.exchange = self._init_exchange()
        self.finnhub_key = Settings.FINNHUB_API_KEY

    # ── Exchange Initialisation ────────────────────────────────────────

    def _init_exchange(self) -> ccxt.Exchange:
        """Initialise the CCXT exchange instance."""
        exchange_class = getattr(ccxt, Settings.EXCHANGE_ID, None)
        if exchange_class is None:
            logger.error("Exchange '%s' not found in CCXT", Settings.EXCHANGE_ID)
            raise ValueError(f"Unsupported exchange: {Settings.EXCHANGE_ID}")

        exchange = exchange_class(
            {
                "apiKey": Settings.BINANCE_API_KEY,
                "secret": Settings.BINANCE_API_SECRET,
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )
        logger.info("Exchange '%s' initialised", Settings.EXCHANGE_ID)
        return exchange

    # ── OHLCV Data ─────────────────────────────────────────────────────

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """Fetch OHLCV candle data and return a DataFrame."""
        timeframe = timeframe or Settings.TIMEFRAME
        limit = limit or Settings.CANDLE_LIMIT

        try:
            raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(
                raw, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df.set_index("timestamp", inplace=True)
            df = df.astype(float)
            logger.info(
                "Fetched %d candles for %s (%s)", len(df), symbol, timeframe
            )
            return df
        except ccxt.BaseError as exc:
            logger.error("CCXT error fetching OHLCV for %s: %s", symbol, exc)
            return pd.DataFrame()

    # ── Ticker / Current Price ─────────────────────────────────────────

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        """Return the latest ticker for *symbol*."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.debug("Ticker %s: last=%.2f", symbol, ticker.get("last", 0))
            return ticker
        except ccxt.BaseError as exc:
            logger.error("Error fetching ticker for %s: %s", symbol, exc)
            return {}

    # ── Crypto News (Finnhub) ──────────────────────────────────────────

    def fetch_crypto_news(self, category: str = "crypto") -> list[dict]:
        """Fetch recent crypto news articles from Finnhub."""
        if not self.finnhub_key:
            logger.warning("Finnhub API key not configured – skipping news fetch")
            return []

        url = "https://finnhub.io/api/v1/news"
        params = {"category": category, "token": self.finnhub_key}

        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            articles = resp.json()
            logger.info("Fetched %d news articles", len(articles))
            return articles
        except requests.RequestException as exc:
            logger.error("Error fetching news: %s", exc)
            return []

    # ── Funding Rate ───────────────────────────────────────────────────

    def fetch_funding_rate(self, symbol: str) -> float | None:
        """Fetch the current funding rate (futures exchanges only)."""
        try:
            if hasattr(self.exchange, "fetch_funding_rate"):
                data = self.exchange.fetch_funding_rate(symbol)
                rate = data.get("fundingRate")
                logger.debug("Funding rate for %s: %s", symbol, rate)
                return rate
        except ccxt.BaseError as exc:
            logger.debug("Funding rate not available for %s: %s", symbol, exc)
        return None

    # ── Volume Profile (simple approximation) ─────────────────────────

    def compute_volume_profile(
        self, df: pd.DataFrame, bins: int = 20
    ) -> pd.DataFrame:
        """Compute a simple volume-by-price profile from OHLCV data."""
        if df.empty:
            return pd.DataFrame()

        price_range = np.linspace(df["low"].min(), df["high"].max(), bins + 1)
        volume_profile: list[dict] = []

        for i in range(len(price_range) - 1):
            lo, hi = price_range[i], price_range[i + 1]
            mask = (df["close"] >= lo) & (df["close"] < hi)
            vol = df.loc[mask, "volume"].sum()
            volume_profile.append(
                {"price_low": lo, "price_high": hi, "volume": vol}
            )

        vp = pd.DataFrame(volume_profile)
        logger.debug("Volume profile computed (%d bins)", bins)
        return vp

    # ── Economic Calendar (placeholder – extend for live feed) ────────

    def fetch_economic_calendar(self) -> list[dict]:
        """Return upcoming high-impact economic events.

        In production, connect to a live economic-calendar API such as
        Forex Factory or Investing.com.  The stub below shows the expected
        data format.
        """
        placeholder: list[dict] = [
            {
                "datetime": datetime.now(timezone.utc).isoformat(),
                "event": "FOMC Meeting Minutes",
                "impact": "HIGH",
                "currency": "USD",
            },
        ]
        logger.debug("Economic calendar: %d events", len(placeholder))
        return placeholder
