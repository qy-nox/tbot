import unittest
from datetime import datetime, timedelta, timezone

import pandas as pd

from core.backtester_professional import ProfessionalBacktester
from core.fundamental_analyzer import EconomicEvent, FundamentalAnalyzer
from core.indicator_engine import IndicatorEngine
from core.price_action import PriceActionAnalyzer
from monitoring.accuracy_tracker import AccuracyTracker
from monitoring.weekly_performance import WeeklyPerformanceTracker
from risk_management.trade_limiter import TradeLimiter
from strategies.multi_confirmation import MultiConfirmationSystem
from strategies.signal_generator import SignalGenerator
from strategies.trend_filters import TrendFilters
from trading.binary_trader import BinaryTrader
from trading.entry_exit_engine import EntryExitEngine


class AdvancedTradingModulesTests(unittest.TestCase):
    def setUp(self):
        base = {
            "open": [100 + i for i in range(80)],
            "high": [102 + i for i in range(80)],
            "low": [99 + i for i in range(80)],
            "close": [101 + i for i in range(80)],
            "volume": [1000 + i * 10 for i in range(80)],
        }
        self.df = pd.DataFrame(base)

    def test_indicator_engine_compute_all(self):
        result = IndicatorEngine().compute_all(self.df)
        self.assertIn("rsi", result)
        self.assertIn("ichimoku", result)
        self.assertIn("vwma", result)

    def test_price_action_analysis(self):
        result = PriceActionAnalyzer().analyze(self.df)
        self.assertIn(result["trend"], {"UPTREND", "DOWNTREND", "SIDEWAYS"})
        self.assertIn("entry_zone", result)

    def test_fundamental_pause_window(self):
        analyzer = FundamentalAnalyzer()
        now = datetime.now(timezone.utc)
        events = [EconomicEvent(name="CPI", timestamp=now + timedelta(minutes=10), impact="HIGH")]
        paused, reason = analyzer.should_pause_trading(now, events)
        self.assertTrue(paused)
        self.assertIn("CPI", reason)

    def test_signal_generator_format(self):
        signal = SignalGenerator().build_signal(
            pair="BTC/USDT",
            timeframe="1h",
            direction="BUY",
            entry_price=100.0,
            stop_loss=95.0,
            tp1=110.0,
            tp2=112.5,
            tp3=115.0,
            confidence=85,
            explanation="test",
            indicators=["RSI", "EMA"],
            pattern="BULLISH_ENGULFING",
        )
        self.assertEqual(signal["pair"], "BTC/USDT")
        self.assertIn("targets", signal)
        self.assertEqual(signal["risk_reward_ratio"], "1:3")

    def test_entry_exit_and_binary(self):
        engine = EntryExitEngine()
        direction, reasons = engine.entry_signal(rsi=20, ema20=101, ema50=100, close=99, bb_lower=100)
        self.assertEqual(direction, "BUY")
        self.assertTrue(reasons)

        binary = BinaryTrader().generate_signal(
            pair="BTC/USDT",
            timeframe="5m",
            rsi=20,
            ema20=101,
            ema50=100,
            close=99,
            bb_upper=120,
            bb_lower=100,
        )
        self.assertIsNotNone(binary)
        self.assertEqual(binary["direction"], "CALL")

    def test_multi_confirmation_and_trend_filters(self):
        checks = {
            "rsi": True,
            "macd": True,
            "ema_alignment": True,
            "volume": True,
        }
        result = MultiConfirmationSystem().evaluate(checks)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["confidence"], 75)

        allowed, _ = TrendFilters().allow_signal(
            direction="BUY",
            trend="UPTREND",
            adx=30,
            macd_line=1,
            atr=1,
            atr_avg_200=100,
            current_volume=200,
            avg_volume_20=100,
        )
        self.assertTrue(allowed)

    def test_backtest_performance_accuracy_and_trade_limits(self):
        metrics = ProfessionalBacktester().summarize([10, -5, 8, -3])
        self.assertEqual(metrics.total_trades, 4)
        self.assertGreater(metrics.win_rate, 0)

        weekly = WeeklyPerformanceTracker().summarize(
            [
                {"pnl": 10.0, "risk_reward": 2.0},
                {"pnl": -5.0, "risk_reward": 1.0},
            ]
        )
        self.assertEqual(weekly["total_signals"], 2)

        tracker = AccuracyTracker()
        tracker.record(pair="BTC/USDT", timeframe="1h", strategy="confluence", won=True)
        tracker.record(pair="BTC/USDT", timeframe="1h", strategy="confluence", won=False)
        self.assertEqual(tracker.win_rate("pair", "BTC/USDT"), 50.0)

        limiter = TradeLimiter()
        now = datetime.now(timezone.utc)
        can_trade, _ = limiter.can_trade(pair="BTC/USDT", now=now)
        self.assertTrue(can_trade)
        limiter.register_trade(pair="BTC/USDT", now=now, won=False)
        can_trade2, _ = limiter.can_trade(pair="BTC/USDT", now=now + timedelta(minutes=10))
        self.assertFalse(can_trade2)


if __name__ == "__main__":
    unittest.main()
