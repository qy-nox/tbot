import unittest
import importlib
from pathlib import Path


class PlatformCompatibilityTests(unittest.TestCase):
    def test_signal_platform_route_modules_import(self):
        from signal_platform.api import routes_admin, routes_auth, routes_performance, routes_signals, routes_subscriptions, routes_users

        self.assertIsNotNone(routes_auth.router)
        self.assertIsNotNone(routes_users.router)
        self.assertIsNotNone(routes_signals.router)
        self.assertIsNotNone(routes_subscriptions.router)
        self.assertIsNotNone(routes_admin.router)
        self.assertIsNotNone(routes_performance.router)

    def test_database_v2_init_db_is_available(self):
        from utils.database_v2 import init_db

        self.assertTrue(callable(init_db))

    def test_new_support_modules_import(self):
        from bots.bot1_subscription.keyboard import plans_keyboard
        from bots.bot1_subscription.utils import format_plan_catalog, format_welcome_message
        from bots.bot2_admin.database import open_session as admin_open_session
        from bots.bot2_admin.keyboard import admin_keyboard
        from bots.bot3_distribution.channel_manager import broadcast_channels_from_env
        from config.bot_config import BotConfig, bot_config
        from database.migrations import run_migrations
        from signal_platform import constants, exceptions, utils
        from utils import helpers, validators

        self.assertEqual(len(plans_keyboard()), 3)
        self.assertIn("Welcome", format_welcome_message())
        self.assertIn("premium", format_plan_catalog())
        self.assertTrue(callable(admin_open_session))
        self.assertEqual(len(admin_keyboard()), 4)
        self.assertIsInstance(broadcast_channels_from_env(), list)
        self.assertIsInstance(bot_config, BotConfig)
        self.assertTrue(callable(run_migrations))
        self.assertEqual(constants.DEFAULT_TIMEZONE, "UTC")
        self.assertTrue(issubclass(exceptions.PlatformError, Exception))
        self.assertTrue(callable(utils.utcnow))
        self.assertTrue(validators.is_valid_email("test@example.com"))
        self.assertEqual(list(helpers.chunks([1, 2, 3], 2)), [[1, 2], [3]])

    def test_dashboard_static_template_exists(self):
        import signal_platform

        static_dashboard = Path(signal_platform.__file__).resolve().parent / "static" / "dashboard.html"
        self.assertTrue(static_dashboard.exists())

    def test_top_level_packages_have_init_files(self):
        repo_root = Path(__file__).resolve().parent.parent
        for package in ("exchanges", "models", "monetization"):
            self.assertTrue((repo_root / package / "__init__.py").exists())
            self.assertIsNotNone(importlib.import_module(package))

    def test_dashboard_route_is_registered(self):
        from fastapi.testclient import TestClient
        from signal_platform.api.app import app

        client = TestClient(app)
        response = client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("Trading Signal Dashboard", response.text)


if __name__ == "__main__":
    unittest.main()
