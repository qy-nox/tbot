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

    def test_settings_startup_validation_flags_bad_token(self):
        import config.settings as settings_module

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "bad", "TELEGRAM_CHAT_ID": "1"}, clear=False):
            reloaded = importlib.reload(settings_module)
            errors = reloaded.Settings.validate_startup_config()
            self.assertTrue(any("TELEGRAM_BOT_TOKEN" in err for err in errors))

        importlib.reload(settings_module)


if __name__ == "__main__":
    unittest.main()
