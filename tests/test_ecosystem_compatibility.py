import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class EcosystemCompatibilityTests(unittest.TestCase):
    def test_requested_files_exist(self):
        repo_root = Path(__file__).resolve().parent.parent
        expected_paths = [
            "bots/bot_main/main.py",
            "bots/bot_main/handlers.py",
            "bots/bot_main/market_data.py",
            "bots/bot_main/signal_display.py",
            "bots/bot_main/keyboard.py",
            "bots/bot_subscription/main.py",
            "bots/bot_subscription/handlers.py",
            "bots/bot_subscription/payment_flow.py",
            "bots/bot_subscription/keyboard.py",
            "bots/bot_subscription/storage.py",
            "signal_platform/static/admin.html",
            "signal_platform/static/admin_dashboard.html",
            "signal_platform/static/admin_style.css",
            "signal_platform/static/admin_script.js",
            "dashboard/backend/api.py",
            "dashboard/backend/models.py",
            "dashboard/backend/services.py",
            "dashboard/frontend/index.html",
            "dashboard/frontend/users.html",
            "dashboard/frontend/subscriptions.html",
            "dashboard/frontend/signals.html",
            "dashboard/frontend/groups.html",
            "dashboard/frontend/channels.html",
            "dashboard/frontend/market.html",
            "dashboard/frontend/demo.html",
            "dashboard/frontend/analytics.html",
            "dashboard/frontend/style.css",
            "dashboard/frontend/app.js",
            "database/models_extended.py",
            "database/migrations/subscriptions.py",
            "database/migrations/groups.py",
            "database/migrations/channels.py",
        ]
        for relative_path in expected_paths:
            self.assertTrue((repo_root / relative_path).exists(), relative_path)

    def test_bot_handlers_basic_contracts(self):
        from bots.bot_main.handlers import handle_help, handle_market, handle_start
        from bots.bot_subscription.handlers import handle_plans, handle_start as sub_start

        self.assertIn("Welcome", handle_start()["text"])
        self.assertIn("/help", handle_help())
        market = handle_market()
        self.assertIsInstance(market, dict)
        self.assertIn("assets", market)
        self.assertIn("trend", market)
        self.assertEqual(len(handle_plans()["keyboard"]), 1)
        self.assertEqual(len(handle_plans()["keyboard"][0]), 3)
        self.assertIn("Welcome", sub_start()["text"])

    def test_dashboard_backend_market_route(self):
        from signal_platform.api.app import app

        client = TestClient(app)
        response = client.get("/dashboard/backend/market")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("assets", payload)
        self.assertIn("trend", payload)

    def test_admin_website_route_exists(self):
        from signal_platform.api.app import app

        client = TestClient(app)
        response = client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("TBOT Admin Dashboard", response.text)


if __name__ == "__main__":
    unittest.main()
