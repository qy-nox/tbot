import importlib
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
        modules = [
            importlib.import_module("bots.bot_main.main"),
            importlib.import_module("bots.bot_subscription.main"),
            importlib.import_module("bots.bot_admin.main"),
        ]

        for module in modules:
            with patch.object(module, "_TELEGRAM_IMPORT_ERROR", ModuleNotFoundError("telegram")):
                with self.assertRaises(RuntimeError):
                    module._ensure_telegram_dependency()


if __name__ == "__main__":
    unittest.main()
