import unittest
import importlib
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pandas as pd

from config.settings import Settings
from core.data_fetcher import DataFetcher
from core.security import ensure_valid_pair
from core.technical_analyzer import TechnicalAnalyzer
from utils.logger import _mask_sensitive_values


class _FakeExchange:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def fetch_ohlcv(self, symbol, timeframe, limit):
        self.calls += 1
        return self.rows


class _TestFetcher(DataFetcher):
    def __init__(self, rows):
        self._rows = rows
        super().__init__()

    def _init_exchange(self):
        return _FakeExchange(self._rows)


class SecurityStabilityTests(unittest.TestCase):
    def test_rsi_handles_zero_loss_without_nan(self):
        closes = [100 + i for i in range(40)]
        df = pd.DataFrame({"close": closes})
        rsi = TechnicalAnalyzer().compute_rsi(df)
        self.assertFalse(pd.isna(rsi.iloc[-1]))
        self.assertGreaterEqual(rsi.iloc[-1], 0.0)
        self.assertLessEqual(rsi.iloc[-1], 100.0)

    def test_trading_pair_validation(self):
        self.assertEqual(ensure_valid_pair("btc/usdt"), "BTC/USDT")
        with self.assertRaises(Exception):
            ensure_valid_pair("BTCUSDT;DROP TABLE")

    def test_ohlcv_cache_reuses_recent_data(self):
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        rows = [[now_ms, 1, 2, 0.5, 1.5, 10] for _ in range(5)]
        fetcher = _TestFetcher(rows)
        old_ttl = Settings.OHLCV_CACHE_TTL_SECONDS
        Settings.OHLCV_CACHE_TTL_SECONDS = 60
        try:
            first = fetcher.fetch_ohlcv("BTC/USDT")
            second = fetcher.fetch_ohlcv("BTC/USDT")
        finally:
            Settings.OHLCV_CACHE_TTL_SECONDS = old_ttl
        self.assertFalse(first.empty)
        self.assertFalse(second.empty)
        self.assertEqual(fetcher.exchange.calls, 1)

    def test_ohlcv_rejects_stale_rows(self):
        stale = datetime.now(timezone.utc) - timedelta(days=3)
        stale_ms = int(stale.timestamp() * 1000)
        rows = [[stale_ms, 1, 2, 0.5, 1.5, 10] for _ in range(5)]
        fetcher = _TestFetcher(rows)
        result = fetcher.fetch_ohlcv("BTC/USDT", timeframe="1h")
        self.assertTrue(result.empty)

    def test_logger_masks_secret_like_content(self):
        masked = _mask_sensitive_values("BINANCE_API_KEY=abc123 TELEGRAM_BOT_TOKEN=def456")
        self.assertNotIn("abc123", masked)
        self.assertNotIn("def456", masked)

    def test_jwt_secret_rejects_known_weak_default(self):
        with patch.dict("os.environ", {"JWT_SECRET": "change-me-in-production"}):
            with self.assertRaises(RuntimeError):
                import signal_platform.auth as auth_mod
                importlib.reload(auth_mod)
        with patch.dict("os.environ", {"JWT_SECRET": "a" * 32}):
            import signal_platform.auth as auth_mod
            importlib.reload(auth_mod)


if __name__ == "__main__":
    unittest.main()
