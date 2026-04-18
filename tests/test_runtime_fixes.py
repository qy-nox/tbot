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

    def test_telegram_notifier_filters_invalid_broadcast_channel_entries(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_CHAT_ID="",
            TELEGRAM_BROADCAST_CHANNELS=["invalid", "-100456"],
        ):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="")
            self.assertTrue(notifier.enabled)
            self.assertEqual(notifier.chat_ids, ["-100456"])

    def test_telegram_notifier_disables_on_invalid_chat_and_no_fallback(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_CHAT_ID="invalid",
            TELEGRAM_BROADCAST_CHANNELS=[],
        ):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="invalid")
            self.assertFalse(notifier.enabled)

    def test_telegram_notifier_falls_back_to_plain_text_on_html_parse_error(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple("notifications.telegram_notifier.Settings", TELEGRAM_BROADCAST_CHANNELS=[]):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="12345")
        self.assertTrue(notifier.enabled)

        failed_html = Mock()
        failed_html.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
        failed_html.status_code = 400
        failed_html.text = "Bad Request: can't parse entities"

        fallback_ok = Mock()
        fallback_ok.raise_for_status.return_value = None
        fallback_ok.status_code = 200
        fallback_ok.text = '{"ok":true}'
        fallback_ok.json.return_value = {"ok": True}

        with patch("notifications.telegram_notifier.requests.post", side_effect=[failed_html, fallback_ok]) as mocked_post:
            self.assertTrue(notifier.send_message("<b>bad < text</b>", parse_mode="HTML"))
            self.assertEqual(mocked_post.call_count, 2)

    def test_telegram_notifier_treats_ok_false_as_failure(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple("notifications.telegram_notifier.Settings", TELEGRAM_BROADCAST_CHANNELS=[]):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="12345")
        self.assertTrue(notifier.enabled)

        response = Mock()
        response.raise_for_status.return_value = None
        response.status_code = 200
        response.text = '{"ok":false,"description":"Bad Request: chat not found"}'
        response.json.return_value = {"ok": False, "description": "Bad Request: chat not found"}

        with patch.multiple("notifications.telegram_notifier.Settings", TELEGRAM_RETRY_ATTEMPTS=1):
            with patch("notifications.telegram_notifier.requests.post", return_value=response):
                self.assertFalse(notifier.send_message("hello"))

    def test_telegram_notifier_treats_non_json_success_body_as_failure(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_BROADCAST_CHANNELS=[],
            TELEGRAM_RETRY_ATTEMPTS=1,
        ):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="12345")
            self.assertTrue(notifier.enabled)

            response = Mock()
            response.raise_for_status.return_value = None
            response.status_code = 200
            response.text = "ok"
            response.json.side_effect = ValueError("not json")

            with patch("notifications.telegram_notifier.requests.post", return_value=response):
                self.assertFalse(notifier.send_message("hello"))

    def test_telegram_notifier_fallback_ok_false_is_failure(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_BROADCAST_CHANNELS=[],
            TELEGRAM_RETRY_ATTEMPTS=1,
        ):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="12345")
            self.assertTrue(notifier.enabled)

            failed_html = Mock()
            failed_html.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
            failed_html.status_code = 400
            failed_html.text = "Bad Request: can't parse entities"

            fallback_ok_false = Mock()
            fallback_ok_false.raise_for_status.return_value = None
            fallback_ok_false.status_code = 200
            fallback_ok_false.text = '{"ok":false,"description":"Bad Request: chat not found"}'
            fallback_ok_false.json.return_value = {
                "ok": False,
                "description": "Bad Request: chat not found",
            }

            with patch(
                "notifications.telegram_notifier.requests.post",
                side_effect=[failed_html, fallback_ok_false],
            ):
                self.assertFalse(notifier.send_message("<b>bad < text</b>", parse_mode="HTML"))

    def test_telegram_notifier_does_not_retry_chat_not_found(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_BROADCAST_CHANNELS=[],
            TELEGRAM_RETRY_ATTEMPTS=3,
        ):
            notifier = TelegramNotifier(token="12345678:abcdefgh", chat_id="-100200")
            self.assertTrue(notifier.enabled)

            chat_not_found_response = Mock()
            chat_not_found_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
            chat_not_found_response.status_code = 400
            chat_not_found_response.text = '{"ok":false,"description":"Bad Request: chat not found"}'
            chat_not_found_response.json.return_value = {"ok": False, "description": "Bad Request: chat not found"}

            with patch("notifications.telegram_notifier.requests.post", return_value=chat_not_found_response) as mocked_post:
                self.assertFalse(notifier.send_message("hello"))
                self.assertEqual(mocked_post.call_count, 1)

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

    def test_settings_startup_validation_flags_placeholder_group_ids(self):
        import config.settings as settings_module

        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "12345:abcdefgh",
                "TELEGRAM_CHAT_ID": "1",
                "SIGNAL_GROUP_1_ID": "-1001234567890",
            },
            clear=False,
        ):
            reloaded = importlib.reload(settings_module)
            errors = reloaded.Settings.validate_startup_config()
            self.assertTrue(any("SIGNAL_GROUP_*_ID" in err for err in errors))
            self.assertEqual(reloaded.Settings.invalid_signal_group_ids(), ["-1001234567890"])

        importlib.reload(settings_module)

    def test_distribution_service_skips_invalid_and_placeholder_group_ids(self):
        from signal_platform.models import DeliveryChannel
        from signal_platform.services import distribution_service

        with patch.multiple(
            "signal_platform.services.distribution_service.Settings",
            TELEGRAM_BROADCAST_CHANNELS=["bad-id", "-1001234567890", "-100200"],
            SIGNAL_GROUP_IDS=["", "-100300", "-1001234567891"],
        ):
            with patch.object(distribution_service, "DISCORD_WEBHOOK_URL", ""):
                targets = distribution_service._broadcast_targets()

        self.assertEqual(
            targets,
            [
                (DeliveryChannel.TELEGRAM, "-100200"),
                (DeliveryChannel.TELEGRAM, "-100300"),
            ],
        )

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
