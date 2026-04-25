"""
Smoke tests for RHIC (Risk/High-Impact Calendar) modules and related fixes.

Tests cover:
  - core/economic_calendar.py
  - core/smc_analyzer.py
  - core/fibonacci.py
  - data_fetcher.py ccxt-optional path
  - StrategyEngine RHIC blackout wiring
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd


def _make_ohlcv(n: int = 100, base_price: float = 100.0) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame with *n* rows."""
    rng = np.random.default_rng(42)
    close = base_price + np.cumsum(rng.normal(0, 1, n))
    close = np.abs(close) + 1  # keep prices positive
    high = close + rng.uniform(0.1, 1.0, n)
    low = close - rng.uniform(0.1, 1.0, n)
    open_ = close + rng.normal(0, 0.5, n)
    volume = rng.uniform(1000, 5000, n)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


# ─────────────────────────────────────────────────────────────────────────────
# EconomicCalendar tests
# ─────────────────────────────────────────────────────────────────────────────


class TestEconomicCalendar(unittest.TestCase):
    def _make_event(self, minutes_from_now: int, impact: str = "high") -> dict:
        event_time = datetime.now(timezone.utc) + timedelta(minutes=minutes_from_now)
        return {
            "datetime": event_time.isoformat(),
            "event": "Test Event",
            "impact": impact,
            "currency": "USD",
        }

    def test_import(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar()
        self.assertIsNotNone(cal)

    def test_no_key_returns_empty_events(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar(finnhub_key="")
        events = cal.fetch_events()
        self.assertIsInstance(events, list)
        self.assertEqual(events, [])

    def test_is_high_impact_window_within_skip_window(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar(finnhub_key="", skip_minutes=30)
        # Inject a cached event 10 minutes from now
        cal._cache = [self._make_event(minutes_from_now=10, impact="high")]
        cal._cache_ts = 999_999_999_999.0  # far in the future → cache valid

        result = cal.is_high_impact_window()
        self.assertTrue(result)

    def test_is_high_impact_window_outside_skip_window(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar(finnhub_key="", skip_minutes=30)
        # Event is 120 minutes away
        cal._cache = [self._make_event(minutes_from_now=120, impact="high")]
        cal._cache_ts = 999_999_999_999.0

        result = cal.is_high_impact_window()
        self.assertFalse(result)

    def test_is_high_impact_window_ignores_low_impact(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar(finnhub_key="", skip_minutes=30)
        # Event is 5 minutes away but low impact
        cal._cache = [self._make_event(minutes_from_now=5, impact="low")]
        cal._cache_ts = 999_999_999_999.0

        result = cal.is_high_impact_window()
        self.assertFalse(result)

    def test_is_high_impact_window_filters_by_currency(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar(finnhub_key="", skip_minutes=30)
        # EUR event 5 min away; we only care about USD
        event = self._make_event(minutes_from_now=5, impact="high")
        event["currency"] = "EUR"
        cal._cache = [event]
        cal._cache_ts = 999_999_999_999.0

        result = cal.is_high_impact_window(currencies=["USD"])
        self.assertFalse(result)

    def test_is_high_impact_window_returns_false_on_exception(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar(finnhub_key="", skip_minutes=30)
        with patch.object(cal, "fetch_events", side_effect=RuntimeError("boom")):
            result = cal.is_high_impact_window()
        self.assertFalse(result)

    def test_upcoming_high_impact_returns_correct_events(self) -> None:
        from core.economic_calendar import EconomicCalendar

        cal = EconomicCalendar(finnhub_key="", skip_minutes=30)
        soon = self._make_event(minutes_from_now=60, impact="high")
        far = self._make_event(minutes_from_now=48 * 60, impact="high")
        cal._cache = [soon, far]
        cal._cache_ts = 999_999_999_999.0

        results = cal.upcoming_high_impact(hours_ahead=24)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["event"], "Test Event")

    def test_normalise_event_handles_epoch_time(self) -> None:
        from core.economic_calendar import EconomicCalendar

        raw = {
            "time": 1_700_000_000,
            "event": "NFP",
            "impact": "high",
            "currency": "USD",
        }
        result = EconomicCalendar._normalise_event(raw)
        self.assertEqual(result["impact"], "high")
        self.assertIn("2023", result["datetime"])  # epoch 1.7B is 2023

    def test_normalise_event_maps_numeric_impact(self) -> None:
        from core.economic_calendar import EconomicCalendar

        raw = {"time": "1700000000", "event": "CPI", "impact": "3", "currency": "USD"}
        result = EconomicCalendar._normalise_event(raw)
        self.assertEqual(result["impact"], "high")


# ─────────────────────────────────────────────────────────────────────────────
# SMCAnalyzer tests
# ─────────────────────────────────────────────────────────────────────────────


class TestSMCAnalyzer(unittest.TestCase):
    def test_import(self) -> None:
        from core.smc_analyzer import SMCAnalyzer

        self.assertIsNotNone(SMCAnalyzer())

    def test_analyse_returns_result_with_synthetic_data(self) -> None:
        from core.smc_analyzer import SMCAnalyzer, SMCResult

        df = _make_ohlcv(120)
        result = SMCAnalyzer().analyse(df)
        self.assertIsInstance(result, SMCResult)
        self.assertIn(result.trend, ("BULLISH", "BEARISH", "NEUTRAL"))
        self.assertIn(result.signal_bias, ("LONG", "SHORT", "NEUTRAL"))
        self.assertIsInstance(result.confidence, float)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)

    def test_analyse_empty_df_returns_neutral(self) -> None:
        from core.smc_analyzer import SMCAnalyzer

        result = SMCAnalyzer().analyse(pd.DataFrame())
        self.assertEqual(result.trend, "NEUTRAL")
        self.assertFalse(result.bos)
        self.assertFalse(result.choch)

    def test_analyse_with_uppercase_columns(self) -> None:
        from core.smc_analyzer import SMCAnalyzer, SMCResult

        df = _make_ohlcv(80)
        df.columns = [c.upper() for c in df.columns]
        result = SMCAnalyzer().analyse(df)
        self.assertIsInstance(result, SMCResult)

    def test_order_blocks_are_detected(self) -> None:
        from core.smc_analyzer import SMCAnalyzer

        df = _make_ohlcv(100)
        result = SMCAnalyzer().analyse(df)
        # Order blocks list should be a list (may be empty for random data)
        self.assertIsInstance(result.order_blocks, list)

    def test_fair_value_gaps_are_detected(self) -> None:
        from core.smc_analyzer import SMCAnalyzer

        df = _make_ohlcv(100)
        result = SMCAnalyzer().analyse(df)
        self.assertIsInstance(result.fair_value_gaps, list)

    def test_reasons_list_is_not_empty_for_trending_data(self) -> None:
        from core.smc_analyzer import SMCAnalyzer

        # Strongly trending up data
        close = [float(i) * 1.01 + 100 for i in range(100)]
        high = [c + 0.5 for c in close]
        low = [c - 0.5 for c in close]
        open_ = [c - 0.1 for c in close]
        volume = [1000.0] * 100
        df = pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": volume}
        )
        result = SMCAnalyzer().analyse(df)
        self.assertGreater(len(result.reasons), 0)


# ─────────────────────────────────────────────────────────────────────────────
# Fibonacci tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFibonacci(unittest.TestCase):
    def test_import(self) -> None:
        import core.fibonacci as fib

        self.assertIsNotNone(fib)

    def test_compute_retracements_basic(self) -> None:
        from core.fibonacci import compute_retracements

        levels = compute_retracements(high=100.0, low=50.0)
        self.assertAlmostEqual(levels["fib_0.0"], 100.0)
        self.assertAlmostEqual(levels["fib_100.0"], 50.0)
        self.assertAlmostEqual(levels["fib_50.0"], 75.0)
        self.assertAlmostEqual(levels["fib_61.8"], 100 - 0.618 * 50)

    def test_compute_retracements_invalid_returns_empty(self) -> None:
        from core.fibonacci import compute_retracements

        levels = compute_retracements(high=50.0, low=100.0)
        self.assertEqual(levels, {})

    def test_compute_extensions(self) -> None:
        from core.fibonacci import compute_extensions

        ext = compute_extensions(high=100.0, low=80.0)
        self.assertIn("fib_ext_161.8", ext)
        self.assertGreater(ext["fib_ext_161.8"], 100.0)

    def test_auto_levels_from_dataframe(self) -> None:
        from core.fibonacci import auto_levels

        df = _make_ohlcv(60)
        levels = auto_levels(df, lookback=30)
        self.assertIn("fib_0.0", levels)
        self.assertIn("fib_61.8", levels)
        self.assertGreater(len(levels), 0)

    def test_auto_levels_with_extensions(self) -> None:
        from core.fibonacci import auto_levels

        df = _make_ohlcv(60)
        levels = auto_levels(df, lookback=30, include_extensions=True)
        self.assertIn("fib_ext_161.8", levels)

    def test_auto_levels_empty_df(self) -> None:
        from core.fibonacci import auto_levels

        levels = auto_levels(pd.DataFrame())
        self.assertEqual(levels, {})

    def test_nearest_level(self) -> None:
        from core.fibonacci import nearest_level

        levels = {"fib_0.0": 100.0, "fib_50.0": 75.0, "fib_100.0": 50.0}
        name, price = nearest_level(74.0, levels)
        self.assertEqual(name, "fib_50.0")

    def test_nearest_level_empty(self) -> None:
        from core.fibonacci import nearest_level

        result = nearest_level(100.0, {})
        self.assertIsNone(result)

    def test_is_near_level(self) -> None:
        from core.fibonacci import is_near_level

        levels = {"fib_61.8": 61.8}
        self.assertTrue(is_near_level(61.8, levels, tolerance_pct=0.01))
        self.assertFalse(is_near_level(70.0, levels, tolerance_pct=0.001))


# ─────────────────────────────────────────────────────────────────────────────
# DataFetcher ccxt-optional path
# ─────────────────────────────────────────────────────────────────────────────


class TestDataFetcherCCXTOptional(unittest.TestCase):
    def test_data_fetcher_imports_without_ccxt(self) -> None:
        """DataFetcher should import even when ccxt is absent."""
        import importlib
        import sys

        # Temporarily hide ccxt
        real_ccxt = sys.modules.get("ccxt")
        sys.modules["ccxt"] = None  # type: ignore[assignment]
        try:
            if "core.data_fetcher" in sys.modules:
                del sys.modules["core.data_fetcher"]
            import core.data_fetcher as df_mod

            self.assertFalse(df_mod._CCXT_AVAILABLE)
        finally:
            if real_ccxt is not None:
                sys.modules["ccxt"] = real_ccxt
            elif "ccxt" in sys.modules:
                del sys.modules["ccxt"]
            # Restore the cached module
            if "core.data_fetcher" in sys.modules:
                del sys.modules["core.data_fetcher"]

    def test_fetch_ohlcv_returns_empty_when_exchange_is_none(self) -> None:
        from core.data_fetcher import DataFetcher

        with patch.object(DataFetcher, "_init_exchange", return_value=None):
            fetcher = DataFetcher()
        result = fetcher.fetch_ohlcv("BTC/USDT")
        self.assertTrue(result.empty)

    def test_fetch_ticker_returns_empty_when_exchange_is_none(self) -> None:
        from core.data_fetcher import DataFetcher

        with patch.object(DataFetcher, "_init_exchange", return_value=None):
            fetcher = DataFetcher()
        result = fetcher.fetch_ticker("BTC/USDT")
        self.assertEqual(result, {})

    def test_fetch_funding_rate_returns_none_when_exchange_is_none(self) -> None:
        from core.data_fetcher import DataFetcher

        with patch.object(DataFetcher, "_init_exchange", return_value=None):
            fetcher = DataFetcher()
        result = fetcher.fetch_funding_rate("BTC/USDT")
        self.assertIsNone(result)


# ─────────────────────────────────────────────────────────────────────────────
# StrategyEngine RHIC wiring
# ─────────────────────────────────────────────────────────────────────────────


class TestStrategyEngineRHIC(unittest.TestCase):
    def _make_analysis(self) -> dict:
        """Return a minimal analysis dict that normally passes all filters."""
        return {
            "rsi": 25.0,
            "ema_fast": 110.0,
            "ema_medium": 105.0,
            "ema_slow": 100.0,
            "macd_line": 1.0,
            "macd_signal": 0.5,
            "macd_histogram": 0.5,
            "bb_upper": 115.0,
            "bb_middle": 110.0,
            "bb_lower": 105.0,
            "atr": 1.0,
            "adx": 30.0,
            "trend": "UPTREND",
            "close": 109.0,
        }

    def test_rhic_blackout_blocks_signal(self) -> None:
        from strategies.strategy_engine import StrategyEngine

        engine = StrategyEngine()

        # Patch calendar to report high-impact window active
        with patch.object(engine.calendar, "is_high_impact_window", return_value=True):
            with patch("config.settings.Settings.CALENDAR_ENABLED", True):
                result = engine._apply_filters(self._make_analysis(), None)
        self.assertFalse(result)

    def test_rhic_blackout_passes_when_no_high_impact(self) -> None:
        from strategies.strategy_engine import StrategyEngine

        engine = StrategyEngine()

        with patch.object(engine.calendar, "is_high_impact_window", return_value=False):
            with patch("config.settings.Settings.CALENDAR_ENABLED", True):
                # Also disable trend/adx filters for this check
                with patch.object(engine, "filters", {"trend_filter": False, "adx_filter": False, "news_filter": False}):
                    result = engine._apply_filters(self._make_analysis(), None)
        self.assertTrue(result)

    def test_rhic_exception_is_non_fatal(self) -> None:
        from strategies.strategy_engine import StrategyEngine

        engine = StrategyEngine()

        with patch.object(engine.calendar, "is_high_impact_window", side_effect=RuntimeError("boom")):
            with patch("config.settings.Settings.CALENDAR_ENABLED", True):
                # Should not raise; calendar errors are non-fatal
                with patch.object(engine, "filters", {"trend_filter": False, "adx_filter": False, "news_filter": False}):
                    result = engine._apply_filters(self._make_analysis(), None)
        # Result should be True (calendar error → allow trade)
        self.assertTrue(result)

    def test_strategy_engine_has_calendar_attribute(self) -> None:
        from strategies.strategy_engine import StrategyEngine
        from core.economic_calendar import EconomicCalendar

        engine = StrategyEngine()
        self.assertIsInstance(engine.calendar, EconomicCalendar)


# ─────────────────────────────────────────────────────────────────────────────
# Core pipeline smoke test
# ─────────────────────────────────────────────────────────────────────────────


class TestCorePipelineSmoke(unittest.TestCase):
    """Smoke test for TechnicalAnalyzer → StrategyEngine pipeline with mocked data."""

    def test_analyse_and_evaluate_with_synthetic_data(self) -> None:
        from core.technical_analyzer import TechnicalAnalyzer
        from strategies.strategy_engine import StrategyEngine

        df = _make_ohlcv(250)
        analyzer = TechnicalAnalyzer()
        analysis = analyzer.analyse(df)
        self.assertIsInstance(analysis, dict)
        self.assertIn("rsi", analysis)
        self.assertIn("trend", analysis)

    def test_fibonacci_levels_in_technical_analyzer(self) -> None:
        from core.technical_analyzer import TechnicalAnalyzer

        df = _make_ohlcv(100)
        analyzer = TechnicalAnalyzer()
        levels = analyzer.compute_fibonacci_levels(df, lookback=50)
        self.assertIn("fib_0", levels)
        self.assertIn("fib_618", levels)
        # fib_0 should be the swing high, fib_100 should be the swing low
        self.assertGreater(levels["fib_0"], levels["fib_100"])

    def test_smc_analyzes_same_df_as_technical_analyzer(self) -> None:
        from core.smc_analyzer import SMCAnalyzer
        from core.technical_analyzer import TechnicalAnalyzer

        df = _make_ohlcv(150)
        ta = TechnicalAnalyzer()
        smc = SMCAnalyzer()

        ta_result = ta.analyse(df)
        smc_result = smc.analyse(df)

        self.assertIsInstance(ta_result, dict)
        self.assertIn("trend", ta_result)
        self.assertIn(smc_result.trend, ("BULLISH", "BEARISH", "NEUTRAL"))


if __name__ == "__main__":
    unittest.main()
