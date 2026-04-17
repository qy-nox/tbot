import importlib
import os
import unittest
from unittest.mock import patch


class ConfigAndCompatibilityTests(unittest.TestCase):
    def test_settings_exposes_new_env_backed_fields(self):
        import config.settings as settings_module

        with patch.dict(
            os.environ,
            {
                "ALPHA_VANTAGE_API_KEY": "alpha",
                "NEWSAPI_KEY": "news",
                "SENTIMENT_ENABLED": "false",
                "CALENDAR_ENABLED": "true",
                "HIGH_IMPACT_SKIP_MINUTES": "45",
                "IQ_OPTION_EMAIL": "bot@example.com",
                "IQ_OPTION_PASSWORD": "secret",
                "POCKET_OPTION_TOKEN": "token",
                "LSTM_ENABLED": "false",
                "XGBOOST_ENABLED": "true",
                "BACKTEST_DAYS": "365",
                "MIN_CONFIRMATIONS": "4",
                "MAX_TRADES_PER_DAY": "6",
                "MAX_POSITIONS": "2",
                "RSI_OVERSOLD": "28",
                "RSI_OVERBOUGHT": "72",
            },
            clear=False,
        ):
            reloaded = importlib.reload(settings_module)
            self.assertEqual(reloaded.Settings.ALPHA_VANTAGE_API_KEY, "alpha")
            self.assertEqual(reloaded.Settings.NEWSAPI_KEY, "news")
            self.assertFalse(reloaded.Settings.SENTIMENT_ENABLED)
            self.assertTrue(reloaded.Settings.CALENDAR_ENABLED)
            self.assertEqual(reloaded.Settings.HIGH_IMPACT_SKIP_MINUTES, 45)
            self.assertEqual(reloaded.Settings.IQ_OPTION_EMAIL, "bot@example.com")
            self.assertFalse(reloaded.Settings.LSTM_ENABLED)
            self.assertTrue(reloaded.Settings.XGBOOST_ENABLED)
            self.assertEqual(reloaded.Settings.BACKTEST_DAYS, 365)
            self.assertEqual(reloaded.Settings.MIN_CONFIRMATIONS, 4)
            self.assertEqual(reloaded.Settings.MAX_TRADES_PER_DAY, 6)
            self.assertEqual(reloaded.Settings.MAX_POSITIONS, 2)
            self.assertEqual(reloaded.Settings.RSI_OVERSOLD, 28)
            self.assertEqual(reloaded.Settings.RSI_OVERBOUGHT, 72)

    def test_backtester_pro_compatibility_import(self):
        from core.backtester_pro import ProfessionalBacktester

        metrics = ProfessionalBacktester().summarize([1.0, -0.5, 2.0])
        self.assertEqual(metrics.total_trades, 3)
        self.assertGreater(metrics.win_rate, 0)
        self.assertGreater(metrics.net_profit, 0)

    def test_binary_handler_configuration(self):
        with patch.dict(
            os.environ,
            {
                "IQ_OPTION_EMAIL": "bot@example.com",
                "IQ_OPTION_PASSWORD": "pw",
                "POCKET_OPTION_TOKEN": "",
            },
            clear=False,
        ):
            import config.settings as settings_module

            importlib.reload(settings_module)
            import core.binary_handler as binary_handler_module

            binary_handler_module = importlib.reload(binary_handler_module)
            BinaryHandler = binary_handler_module.BinaryHandler

            self.assertTrue(BinaryHandler().configured())

    def test_binary_handler_not_configured(self):
        with patch.dict(
            os.environ,
            {
                "IQ_OPTION_EMAIL": "",
                "IQ_OPTION_PASSWORD": "",
                "POCKET_OPTION_TOKEN": "",
            },
            clear=False,
        ):
            import config.settings as settings_module

            importlib.reload(settings_module)
            import core.binary_handler as binary_handler_module

            binary_handler_module = importlib.reload(binary_handler_module)
            BinaryHandler = binary_handler_module.BinaryHandler

            self.assertFalse(BinaryHandler().configured())


if __name__ == "__main__":
    unittest.main()
