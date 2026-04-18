import importlib
import os
import unittest
from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient


class RuntimeFixesTests(unittest.TestCase):
    def test_dashboard_polling_endpoint_returns_expected_shape(self):
        from signal_platform.api.app import app

        client = TestClient(app)
        response = client.get("/dashboard/api/signals")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in ("total_signals", "recent", "updated", "won", "lost"):
            self.assertIn(key, payload)
        self.assertIsInstance(payload["recent"], list)

    def test_health_endpoint_reports_database_status(self):
        from signal_platform.api.app import app

        client = TestClient(app)
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(payload["status"], ("ok", "degraded"))
        self.assertIn(payload["database"], ("ok", "error"))

    def test_telegram_notifier_retries_failed_send(self):
        from notifications.telegram_notifier import TelegramNotifier

        notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="12345")
        self.assertTrue(notifier.enabled)

        response = Mock()
        response.raise_for_status.side_effect = requests.RequestException("network")
        with patch("notifications.telegram_notifier.requests.post", return_value=response) as mocked_post:
            self.assertFalse(notifier.send_message("hello"))
            self.assertEqual(mocked_post.call_count, 3)

    def test_telegram_notifier_uses_broadcast_channels_when_primary_missing(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_CHAT_ID="",
            TELEGRAM_BROADCAST_CHANNELS=["-100123", "-100456"],
        ):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="")
            self.assertTrue(notifier.enabled)
            self.assertEqual(notifier.chat_id, "-100123")
            self.assertEqual(notifier.chat_ids, ["-100123", "-100456"])

    def test_telegram_notifier_disables_on_invalid_chat_and_no_fallback(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_CHAT_ID="invalid",
            TELEGRAM_BROADCAST_CHANNELS=[],
        ):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="invalid")
            self.assertFalse(notifier.enabled)

    def test_start_api_skips_boot_when_port_is_busy(self):
        from main import start_api

        with patch.dict(os.environ, {"API_HOST": "0.0.0.0", "API_PORT": "8000"}, clear=False):
            with patch("main._release_port_if_needed", return_value=False):
                with patch("signal_platform.models.init_db") as platform_init:
                    with patch("uvicorn.run") as uvicorn_run:
                        start_api()
                        platform_init.assert_called_once()
                        uvicorn_run.assert_not_called()

    def test_release_port_does_not_kill_when_force_kill_disabled(self):
        from main import _release_port_if_needed

        with patch.dict(os.environ, {"API_FORCE_KILL_PORT": "false"}, clear=False):
            with patch("main._is_port_available", return_value=False):
                with patch("main._port_owner_pids") as owner_pids:
                    self.assertFalse(_release_port_if_needed("0.0.0.0", 8000))
                    owner_pids.assert_not_called()

    def test_release_port_skips_non_tbot_processes(self):
        from main import _release_port_if_needed

        with patch.dict(os.environ, {"API_FORCE_KILL_PORT": "true"}, clear=False):
            with patch("main._is_port_available", return_value=False):
                with patch("main._port_owner_pids", return_value=[1234]):
                    with patch("main._pid_belongs_to_tbot", return_value=False):
                        with patch("main.os.kill") as kill_mock:
                            self.assertFalse(_release_port_if_needed("0.0.0.0", 8000, wait_seconds=0.1))
                            kill_mock.assert_not_called()

    def test_settings_startup_validation_flags_bad_token(self):
        import config.settings as settings_module

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "bad", "TELEGRAM_CHAT_ID": "1"}, clear=False):
            reloaded = importlib.reload(settings_module)
            errors = reloaded.Settings.validate_startup_config()
            self.assertTrue(any("TELEGRAM_BOT_TOKEN" in err for err in errors))
            self.assertFalse(reloaded.is_valid_telegram_token("bad"))
            self.assertTrue(reloaded.is_valid_telegram_token("12345:abcdefgh"))

        importlib.reload(settings_module)

    def test_fallback_signal_generated_for_aligned_trend(self):
        from main import TradingBot

        analysis = {
            "trend": "UPTREND",
            "close": 100.0,
            "atr": 2.0,
            "ema_fast": 105.0,
            "ema_medium": 100.0,
        }
        signal = TradingBot._fallback_signal("BTC/USDT", analysis)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, "BUY")
        self.assertGreater(signal.take_profit_1, signal.entry_price)
        self.assertLess(signal.stop_loss, signal.entry_price)

    def test_fallback_signal_not_generated_for_invalid_input(self):
        from main import TradingBot

        self.assertIsNone(TradingBot._fallback_signal("BTC/USDT", {"trend": "SIDEWAYS"}))
        self.assertIsNone(
            TradingBot._fallback_signal(
                "BTC/USDT",
                {"trend": "UPTREND", "close": 100.0, "atr": 1.0, "ema_fast": None, "ema_medium": 90.0},
            )
        )


if __name__ == "__main__":
    unittest.main()
