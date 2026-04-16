import os
import unittest
from unittest.mock import patch


class BotEntrypointTests(unittest.TestCase):
    def test_main_bot_token_validation(self):
        from bots.bot_main.main import _require_token

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_MAIN": "bad-token"}, clear=False):
            with self.assertRaises(RuntimeError):
                _require_token()

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_MAIN": "12345:abcde"}, clear=False):
            self.assertEqual(_require_token(), "12345:abcde")

    def test_subscription_bot_token_validation(self):
        from bots.bot_subscription.main import _require_token

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_SUB": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                _require_token()

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_SUB": "12345:abcde"}, clear=False):
            self.assertEqual(_require_token(), "12345:abcde")

    def test_admin_ids_parser(self):
        from bots.bot_admin.main import _admin_ids

        with patch.dict(os.environ, {"ADMIN_USER_IDS": "1, 2, x,3", "ADMIN_IDS": ""}, clear=False):
            self.assertEqual(_admin_ids(), {1, 2, 3})

    def test_bots_raise_clear_error_when_telegram_dependency_missing(self):
        from bots.bot_admin.main import _ensure_telegram_dependency as ensure_admin
        from bots.bot_main.main import _ensure_telegram_dependency as ensure_main
        from bots.bot_subscription.main import _ensure_telegram_dependency as ensure_sub

        for ensure in (ensure_main, ensure_sub, ensure_admin):
            with self.assertRaises(RuntimeError):
                ensure()


if __name__ == "__main__":
    unittest.main()
