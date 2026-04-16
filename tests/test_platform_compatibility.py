import unittest


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


if __name__ == "__main__":
    unittest.main()
