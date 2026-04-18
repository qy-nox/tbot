import unittest


class TelegramEcosystemDeliverablesTests(unittest.TestCase):
    def test_signal_engine_grades(self):
        from bots.main_signal_bot.signal_engine import SignalEngine

        self.assertEqual(SignalEngine.evaluate(confirmations=1, confidence=0.60).grade, "B")
        self.assertEqual(SignalEngine.evaluate(confirmations=3, confidence=0.80).grade, "A")
        self.assertEqual(SignalEngine.evaluate(confirmations=5, confidence=0.95).grade, "A+")

    def test_managed_group_count(self):
        from bots.main_signal_bot.distribution import MANAGED_GROUPS, target_groups

        self.assertEqual(len(MANAGED_GROUPS), 12)
        self.assertEqual(len(target_groups(signal_type="crypto", grade="A+")), 2)

    def test_compatibility_service_helpers(self):
        from services.distribution_service import select_target_groups
        from services.payment_service import ALLOWED_METHODS

        self.assertIn("bkash", ALLOWED_METHODS)
        self.assertEqual(len(select_target_groups(signal_type="binary", grade="B")), 2)


if __name__ == "__main__":
    unittest.main()
