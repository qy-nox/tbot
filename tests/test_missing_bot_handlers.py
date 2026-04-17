import unittest


class MissingBotHandlersTests(unittest.TestCase):
    def test_market_data_fallback(self):
        from bots.bot_main.market_data import get_live_market_status

        payload = get_live_market_status()
        self.assertIn("assets", payload)
        self.assertIn("trend", payload)
        self.assertIn(payload["trend"], {"BULLISH", "BEARISH", "UNKNOWN"})

    def test_signal_display_fallback(self):
        from bots.bot_main.signal_display import format_signal_list

        self.assertEqual(format_signal_list([]), "📊 No active signals")

    def test_subscription_modules_contract(self):
        from bots.bot_subscription.keyboard import continue_keyboard, payment_options_keyboard, plans_keyboard
        from bots.bot_subscription.payment_flow import begin_subscription, submit_transaction
        from bots.bot_subscription.storage import get_application

        self.assertEqual(plans_keyboard(), [["Free", "Premium", "VIP"]])
        self.assertEqual(continue_keyboard(), [["Continue"]])
        self.assertEqual(payment_options_keyboard(), [["Card", "Crypto"]])
        begin_subscription(username="u1", user_id=1, telegram_id="1", plan="premium")
        self.assertIsNotNone(get_application(1))
        self.assertEqual(submit_transaction(1, "tx"), "✅ Payment confirmed")

if __name__ == "__main__":
    unittest.main()
