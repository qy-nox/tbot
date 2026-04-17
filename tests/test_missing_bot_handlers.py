import unittest


class MissingBotHandlersTests(unittest.TestCase):
    def test_market_data_fallback(self):
        from bots.bot_main.market_data import get_live_market_status

        payload = get_live_market_status()
        self.assertIn("assets", payload)
        self.assertIn("trend", payload)
        self.assertEqual(payload["trend"], "BULLISH")

    def test_signal_display_fallback(self):
        from bots.bot_main.signal_display import format_signal_list

        self.assertEqual(format_signal_list([]), "📊 No active signals")

    def test_subscription_modules_contract(self):
        from bots.bot_subscription.keyboard import continue_keyboard, payment_options_keyboard, plans_keyboard
        from bots.bot_subscription.payment_flow import submit_transaction
        from bots.bot_subscription.storage import get_application

        self.assertEqual(plans_keyboard(), [["Free", "Premium", "VIP"]])
        self.assertEqual(continue_keyboard(), [["Continue"]])
        self.assertEqual(payment_options_keyboard(), [["Card", "Crypto"]])
        self.assertIsNone(get_application(1))
        self.assertEqual(submit_transaction(1, "tx"), "✅ Payment confirmed")

    def test_admin_modules_contract(self):
        from bots.bot_admin.keyboard import admin_panel_keyboard
        from bots.bot_admin.payment_approval import approve_payment, pending_payments, reject_payment
        from bots.bot_admin.user_management import ban_user, list_users, unban_user

        self.assertEqual(admin_panel_keyboard(), [["Payments", "Users"], ["Stats", "Groups"]])
        self.assertEqual(pending_payments(None), [])
        self.assertIsNone(approve_payment(None, 1, "tx"))
        self.assertEqual(reject_payment(None, 1), "❌ Payment rejected")
        self.assertEqual(list_users(None), [])
        self.assertIsNone(ban_user(None, 1))
        self.assertIsNone(unban_user(None, 1))


if __name__ == "__main__":
    unittest.main()
