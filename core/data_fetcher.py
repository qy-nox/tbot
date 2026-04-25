"""
Data fetching module for the trading bot.
Retrieves OHLCV data, crypto news, economic calendar events,
funding rates, and volume profiles from various sources.
"""

import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

try:
    import ccxt
    _CCXT_AVAILABLE = True
except ImportError:  # pragma: no cover - ccxt is optional
    ccxt = None  # type: ignore[assignment]
    _CCXT_AVAILABLE = False

import numpy as np
import pandas as pd
import requests

from config.settings import Settings
from core.security import ensure_valid_pair
from utils.validators import validate_required_columns

logger = logging.getLogger("trading_bot.data_fetcher")
RATE_LIMIT_TIMING_BUFFER_SECONDS = 0.01
RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
DEFAULT_CIRCUIT_BREAKER_COOLDOWN_SECONDS = 30


class DataFetcher:
    """Fetches market data from exchanges and external APIs."""

    def __init__(self) -> None:
        self.exchange = self._init_exchange()
        self.finnhub_key = Settings.FINNHUB_API_KEY
        self._ohlcv_cache: dict[tuple[str, str, int], tuple[float, pd.DataFrame]] = {}
        self._http_cache: dict[str, tuple[float, Any]] = {}
        self._cache_lock = threading.Lock()
        self._request_times: deque[float] = deque()
        self._circuit_failure_count = 0
        self._circuit_open_until = 0.0

    # ── Exchange Initialisation ────────────────────────────────────────

    def _init_exchange(self):
        """Initialise the CCXT exchange instance.

        Returns ``None`` (and logs a warning) when the ``ccxt`` package
        is not installed, so the bot can still start in environments where
        ccxt is absent (e.g. test runners without the full dependency set).
        """
        if not _CCXT_AVAILABLE:
            logger.warning(
                "ccxt is not installed – exchange connectivity unavailable. "
                "Install ccxt to enable live market data."
            )
            return None

        exchange_class = getattr(ccxt, Settings.EXCHANGE_ID, None)
        if exchange_class is None:
            logger.error("Exchange '%s' not found in CCXT", Settings.EXCHANGE_ID)
            return None

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
        if self.exchange is None:
            logger.warning("Exchange not available; cannot fetch OHLCV for %s", symbol)
            return pd.DataFrame()
        symbol = ensure_valid_pair(symbol)
        if self._is_circuit_open():
            logger.warning("Circuit breaker open; skipping OHLCV fetch for %s", symbol)
            return pd.DataFrame()
        timeframe = timeframe or Settings.TIMEFRAME
        limit = limit or Settings.CANDLE_LIMIT
        cache_key = (symbol, timeframe, limit)
        with self._cache_lock:
            cached = self._ohlcv_cache.get(cache_key)
            now = time.time()
            if cached and now - cached[0] <= Settings.OHLCV_CACHE_TTL_SECONDS:
                return cached[1].copy()

        # Build tuple of transient CCXT exceptions to retry on (guards against missing ccxt)
        _transient_exc: tuple[type[Exception], ...] = (OSError,)
        _base_exc: tuple[type[Exception], ...] = (Exception,)
        if _CCXT_AVAILABLE:
            _transient_exc = (ccxt.RateLimitExceeded, ccxt.NetworkError, ccxt.RequestTimeout)
            _base_exc = (ccxt.BaseError,)

        for attempt in range(1, Settings.EXCHANGE_RETRY_ATTEMPTS + 1):
            try:
                self._respect_rate_limit()
                raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                df = pd.DataFrame(
                    raw, columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
                validate_required_columns(df.columns, ("timestamp", "open", "high", "low", "close", "volume"))
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
                df.set_index("timestamp", inplace=True)
                df = df.astype(float)
                if not self._validate_ohlcv_data(df):
                    logger.warning("Invalid OHLCV data for %s (%s)", symbol, timeframe)
                    self._record_circuit_failure()
                    return pd.DataFrame()
                if self._is_stale(df, timeframe):
                    logger.warning("Discarded stale OHLCV data for %s (%s)", symbol, timeframe)
                    return pd.DataFrame()
                with self._cache_lock:
                    if len(self._ohlcv_cache) >= Settings.OHLCV_CACHE_MAX_ENTRIES:
                        oldest_key = min(self._ohlcv_cache, key=lambda k: self._ohlcv_cache[k][0])
                        self._ohlcv_cache.pop(oldest_key, None)
                    self._ohlcv_cache[cache_key] = (time.time(), df.copy())
                self._record_circuit_success()
                logger.info("Fetched %d candles for %s (%s)", len(df), symbol, timeframe)
                return df
            except _transient_exc as exc:
                self._record_circuit_failure()
                if attempt >= Settings.EXCHANGE_RETRY_ATTEMPTS:
                    logger.error("Transient exchange error fetching OHLCV for %s: %s", symbol, exc)
                    return pd.DataFrame()
                delay = min(Settings.EXCHANGE_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)), 30.0)
                logger.warning("Retrying OHLCV fetch for %s in %.2fs (%s)", symbol, delay, exc)
                time.sleep(delay)
            except _base_exc as exc:
                self._record_circuit_failure()
                logger.error("CCXT error fetching OHLCV for %s: %s", symbol, exc)
                return pd.DataFrame()

        return pd.DataFrame()

    @staticmethod
    def _timeframe_to_seconds(timeframe: str) -> int:
        unit = timeframe[-1]
        try:
            value = int(timeframe[:-1])
        except ValueError:
            logger.warning("Invalid timeframe format: %s", timeframe)
            return 0
        scale = {"m": 60, "h": 3600, "d": 86400}.get(unit, 0)
        return value * scale

    def _is_stale(self, df: pd.DataFrame, timeframe: str) -> bool:
        if df.empty:
            return True
        if df.index.tz is None:
            return True
        latest_ts = df.index[-1]
        tf_seconds = self._timeframe_to_seconds(timeframe)
        if tf_seconds <= 0:
            return False
        data_age_seconds = (datetime.now(timezone.utc) - latest_ts.to_pydatetime()).total_seconds()
        return data_age_seconds > tf_seconds * 3

    # ── Ticker / Current Price ─────────────────────────────────────────

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        """Return the latest ticker for *symbol*."""
        if self.exchange is None:
            logger.warning("Exchange not available; cannot fetch ticker for %s", symbol)
            return {}
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.debug("Ticker %s: last=%.2f", symbol, ticker.get("last", 0))
            return ticker
        except Exception as exc:
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
        cache_key = f"finnhub:{category}"
        payload = self._request_json_with_retry(url, params=params, cache_key=cache_key, ttl_seconds=120)
        if isinstance(payload, list):
            logger.info("Fetched %d news articles", len(payload))
            return payload
        return []

    # ── Funding Rate ───────────────────────────────────────────────────

    def fetch_funding_rate(self, symbol: str) -> float | None:
        """Fetch the current funding rate (futures exchanges only)."""
        if self.exchange is None:
            return None
        try:
            if hasattr(self.exchange, "fetch_funding_rate"):
                data = self.exchange.fetch_funding_rate(symbol)
                rate = data.get("fundingRate")
                logger.debug("Funding rate for %s: %s", symbol, rate)
                return rate
        except Exception as exc:
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

    def fetch_coingecko_market_snapshot(self, symbol: str) -> dict[str, Any]:
        """Fetch market-cap and volume validation data from CoinGecko."""
        coin_id = self._resolve_coingecko_id(symbol)
        if not coin_id:
            return {}
        payload = self._request_json_with_retry(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency": "usd", "ids": coin_id},
            cache_key=f"coingecko:{coin_id}",
            ttl_seconds=180,
        )
        if not isinstance(payload, list) or not payload:
            return {}
        item = payload[0]
        market_cap = item.get("market_cap")
        total_volume = item.get("total_volume")
        if not isinstance(market_cap, (int, float)) or market_cap < 0:
            return {}
        if not isinstance(total_volume, (int, float)) or total_volume < 0:
            return {}
        return {
            "id": item.get("id"),
            "symbol": item.get("symbol"),
            "name": item.get("name"),
            "market_cap": float(market_cap),
            "total_volume": float(total_volume),
            "price_change_percentage_24h": item.get("price_change_percentage_24h"),
        }

    def fetch_coinglass_sentiment(self, symbol: str = "BTC") -> dict[str, Any]:
        """Fetch derivatives sentiment data from Coinglass API."""
        api_key = getattr(Settings, "COINGLASS_API_KEY", "")
        if not api_key:
            return {}
        payload = self._request_json_with_retry(
            "https://open-api.coinglass.com/api/pro/v1/futures/funding_rates_chart",
            params={"symbol": symbol.upper()},
            headers={"CG-API-KEY": api_key},
            cache_key=f"coinglass:{symbol.upper()}",
            ttl_seconds=90,
        )
        if not isinstance(payload, dict):
            return {}
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        return payload

    def fetch_alpha_vantage_fx(self, from_currency: str = "USD", to_currency: str = "EUR") -> dict[str, Any]:
        """Fetch forex reference data from Alpha Vantage for macro correlation checks."""
        api_key = Settings.ALPHA_VANTAGE_API_KEY
        if not api_key:
            return {}
        payload = self._request_json_with_retry(
            "https://www.alphavantage.co/query",
            params={
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_currency.upper(),
                "to_currency": to_currency.upper(),
                "apikey": api_key,
            },
            cache_key=f"alphavantage:{from_currency.upper()}:{to_currency.upper()}",
            ttl_seconds=300,
        )
        if not isinstance(payload, dict):
            return {}
        data = payload.get("Realtime Currency Exchange Rate")
        return data if isinstance(data, dict) else {}

    def _request_json_with_retry(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        cache_key: str | None = None,
        ttl_seconds: int = 0,
    ) -> Any:
        if cache_key and ttl_seconds > 0:
            with self._cache_lock:
                cached = self._http_cache.get(cache_key)
                if cached and (time.time() - cached[0]) <= ttl_seconds:
                    return cached[1]

        if self._is_circuit_open():
            return None

        for attempt in range(1, Settings.EXCHANGE_RETRY_ATTEMPTS + 1):
            try:
                self._respect_rate_limit()
                resp = requests.get(url, params=params, headers=headers, timeout=10)
                resp.raise_for_status()
                payload = resp.json()
                if cache_key and ttl_seconds > 0:
                    with self._cache_lock:
                        self._http_cache[cache_key] = (time.time(), payload)
                self._record_circuit_success()
                return payload
            except (requests.RequestException, ValueError) as exc:
                self._record_circuit_failure()
                if attempt >= Settings.EXCHANGE_RETRY_ATTEMPTS:
                    logger.error("HTTP API request failed for %s: %s", url, exc)
                    return None
                delay = min(Settings.EXCHANGE_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)), 30.0)
                time.sleep(delay)
        return None

    @staticmethod
    def _resolve_coingecko_id(symbol: str) -> str:
        base = ensure_valid_pair(symbol).split("/", 1)[0].lower() if "/" in symbol else symbol.strip().lower()
        mappings = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "bnb": "binancecoin",
            "sol": "solana",
            "xrp": "ripple",
            "ada": "cardano",
            "doge": "dogecoin",
        }
        return mappings.get(base, "")

    def _respect_rate_limit(self) -> None:
        max_per_minute = max(1, int(Settings.API_RATE_LIMIT_PER_MINUTE))
        while True:
            now = time.time()
            with self._cache_lock:
                while self._request_times and (now - self._request_times[0]) >= RATE_LIMIT_WINDOW_SECONDS:
                    self._request_times.popleft()
                if len(self._request_times) < max_per_minute:
                    self._request_times.append(float(now))
                    return
                sleep_for = max(0.0, RATE_LIMIT_WINDOW_SECONDS - (now - self._request_times[0])) + RATE_LIMIT_TIMING_BUFFER_SECONDS
            time.sleep(sleep_for)

    def _is_circuit_open(self) -> bool:
        return time.time() < self._circuit_open_until

    def _record_circuit_success(self) -> None:
        self._circuit_failure_count = 0
        self._circuit_open_until = 0.0

    def _record_circuit_failure(self) -> None:
        self._circuit_failure_count += 1
        threshold = max(
            1,
            int(getattr(Settings, "CIRCUIT_BREAKER_FAILURE_THRESHOLD", DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD)),
        )
        if self._circuit_failure_count >= threshold:
            cooldown = max(
                1,
                int(getattr(Settings, "CIRCUIT_BREAKER_COOLDOWN_SECONDS", DEFAULT_CIRCUIT_BREAKER_COOLDOWN_SECONDS)),
            )
            self._circuit_open_until = time.time() + cooldown

    @staticmethod
    def _validate_ohlcv_data(df: pd.DataFrame) -> bool:
        if df.empty:
            return False
        required = ("open", "high", "low", "close", "volume")
        if any(col not in df.columns for col in required):
            return False
        numeric = df.loc[:, required]
        if not np.isfinite(numeric.to_numpy()).all():
            return False
        if (numeric[["open", "high", "low", "close"]] < 0).values.any():
            return False
        if (numeric["volume"] < 0).any():
            return False
        if (numeric["high"] < numeric["low"]).any():
            return False
        return True
