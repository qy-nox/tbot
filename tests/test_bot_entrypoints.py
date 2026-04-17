import importlib
import os
import unittest
from unittest.mock import patch


class BotEntrypointTests(unittest.TestCase):
    def test_bot1_subscription_entrypoint_delegates_to_subscription_bot(self):
        from bots.bot1_subscription import main as bot1_main

        with patch("bots.bot1_subscription.main.subscription_main.main") as canonical_main:
            bot1_main.main()
            canonical_main.assert_called_once()

    def test_bot2_admin_entrypoint_delegates_to_admin_bot(self):
        from bots.bot2_admin import main as bot2_main

        with patch("bots.bot2_admin.main.admin_main.main") as canonical_main:
            bot2_main.main()
            canonical_main.assert_called_once()

    def test_settings_bot_token_aliases(self):
        import config.settings as settings_module

        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "111:base",
                "BOT1_SUBSCRIPTION_TOKEN": "222:sub",
                "BOT2_ADMIN_TOKEN": "333:admin",
            },
            clear=True,
        ):
            reloaded = importlib.reload(settings_module)
            self.assertEqual(reloaded.Settings.TELEGRAM_BOT_TOKEN_MAIN, "111:base")
            self.assertEqual(reloaded.Settings.TELEGRAM_BOT_TOKEN_SUB, "222:sub")
            self.assertEqual(reloaded.Settings.TELEGRAM_BOT_TOKEN_ADMIN, "333:admin")

        with patch.dict(
            os.environ,
            {
                "TELEGRAM_BOT_TOKEN": "111:base",
                "TELEGRAM_BOT_TOKEN_MAIN": "",
                "TELEGRAM_BOT_TOKEN_SUB": "",
                "BOT1_SUBSCRIPTION_TOKEN": "222:sub",
                "TELEGRAM_BOT_TOKEN_ADMIN": "",
                "BOT2_ADMIN_TOKEN": "333:admin",
            },
            clear=False,
        ):
            reloaded = importlib.reload(settings_module)
            self.assertEqual(reloaded.Settings.TELEGRAM_BOT_TOKEN_MAIN, "111:base")
            self.assertEqual(reloaded.Settings.TELEGRAM_BOT_TOKEN_SUB, "222:sub")
            self.assertEqual(reloaded.Settings.TELEGRAM_BOT_TOKEN_ADMIN, "333:admin")

        importlib.reload(settings_module)

    def test_main_bot_token_validation(self):
        from bots.bot_main.main import _require_token

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_MAIN": "bad-token"}, clear=False):
            self.assertIsNone(_require_token())

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_MAIN": "12345:abcde"}, clear=False):
            self.assertEqual(_require_token(), "12345:abcde")

    def test_subscription_bot_token_validation(self):
        from bots.bot_subscription.main import _require_token

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_SUB": ""}, clear=False):
            self.assertIsNone(_require_token())

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_SUB": "12345:abcde"}, clear=False):
            self.assertEqual(_require_token(), "12345:abcde")

    def test_admin_bot_token_validation(self):
        from bots.bot_admin.main import _require_token

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_ADMIN": ""}, clear=False):
            self.assertIsNone(_require_token())

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_ADMIN": "12345:abcde"}, clear=False):
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

    def test_run_manager_skips_bots_without_token(self):
        from run import BotManager

        manager = BotManager()
        main_bot = next(bot for bot in manager.bots if bot["name"] == "📊 Bot 1: Main Signal Bot")

        with patch.object(manager, "_load_env_file", return_value={}):
            with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_MAIN": "", "TELEGRAM_BOT_TOKEN": ""}, clear=False):
                self.assertIsNone(manager._get_bot_token(main_bot))

        with patch.object(manager, "_load_env_file", return_value={}):
            with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN_MAIN": "12345:abcde"}, clear=False):
                self.assertEqual(manager._get_bot_token(main_bot), "12345:abcde")


if __name__ == "__main__":
    unittest.main()
