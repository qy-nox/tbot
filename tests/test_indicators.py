import unittest

import pandas as pd

from core.advanced_indicators import AdvancedIndicators


class TestAdvancedIndicators(unittest.TestCase):
    def test_compute_all_contains_indicator_count(self):
        df = pd.DataFrame(
            {
                "open": [1 + i * 0.1 for i in range(260)],
                "high": [1.1 + i * 0.1 for i in range(260)],
                "low": [0.9 + i * 0.1 for i in range(260)],
                "close": [1 + i * 0.1 for i in range(260)],
                "volume": [1000 + i for i in range(260)],
            }
        )
        data = AdvancedIndicators().compute_all(df)
        self.assertGreaterEqual(data["indicator_count"], 50)


if __name__ == "__main__":
    unittest.main()
