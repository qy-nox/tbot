import unittest
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
        from bots.bot2_admin.database import open_session as admin_open_session
        from config.bot_config import BotConfig, bot_config
        from database.migrations import run_migrations
        from signal_platform import constants, exceptions, utils
        from utils import helpers, validators

        self.assertTrue(callable(admin_open_session))
        self.assertIsInstance(bot_config, BotConfig)
        self.assertTrue(callable(run_migrations))
        self.assertEqual(constants.DEFAULT_TIMEZONE, "UTC")
        self.assertTrue(issubclass(exceptions.PlatformError, Exception))
        self.assertTrue(callable(utils.utcnow))
        self.assertTrue(validators.is_valid_email("test@example.com"))
        self.assertEqual(list(helpers.chunks([1, 2, 3], 2)), [[1, 2], [3]])

    def test_dashboard_static_template_exists(self):
        static_dashboard = Path("/home/runner/work/tbot/tbot/signal_platform/static/dashboard.html")
        self.assertTrue(static_dashboard.exists())


if __name__ == "__main__":
    unittest.main()
