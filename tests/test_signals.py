import unittest

from strategies.signal_grader import grade_signal
from strategies.signal_validator import validate_signal


class TestSignals(unittest.TestCase):
    def test_signal_grading(self):
        self.assertEqual(grade_signal(0.96), "A+++")
        self.assertEqual(grade_signal(0.65), "B")

    def test_signal_validation(self):
        self.assertTrue(validate_signal({"pair": "BTC/USDT", "direction": "BUY", "entry_price": 1.0}))
        self.assertFalse(validate_signal({"pair": "BTC/USDT"}))


if __name__ == "__main__":
    unittest.main()
