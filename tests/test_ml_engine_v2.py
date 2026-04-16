import unittest

import pandas as pd

from core.advanced_ml_engine_v2 import AdvancedMLEngineV2


class TestAdvancedMLEngineV2(unittest.TestCase):
    def _sample_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "open": [100 + i * 0.2 for i in range(240)],
                "high": [101 + i * 0.2 for i in range(240)],
                "low": [99 + i * 0.2 for i in range(240)],
                "close": [100 + i * 0.2 + (0.3 if i % 2 else -0.1) for i in range(240)],
                "volume": [1000 + (i * 3) for i in range(240)],
            }
        )

    def test_predict_returns_seven_model_votes(self):
        engine = AdvancedMLEngineV2()
        prediction = engine.predict(self._sample_df())

        self.assertIsNotNone(prediction)
        self.assertEqual(len(prediction.votes), 7)
        self.assertIn(prediction.regime, {"TRENDING", "RANGING", "VOLATILE"})
        self.assertGreaterEqual(prediction.confidence, 0.0)
        self.assertLessEqual(prediction.confidence, 1.0)

    def test_positive_reinforcement_increases_confidence(self):
        engine = AdvancedMLEngineV2()
        df = self._sample_df()
        before = engine.predict(df)
        self.assertIsNotNone(before)

        engine.record_outcome(before.direction, pnl=1.0)
        after = engine.predict(df)
        self.assertIsNotNone(after)
        self.assertEqual(after.direction, before.direction)
        self.assertGreaterEqual(after.confidence, before.confidence)

    def test_negative_reinforcement_reduces_confidence(self):
        engine = AdvancedMLEngineV2()
        df = self._sample_df()
        before = engine.predict(df)
        self.assertIsNotNone(before)

        engine.record_outcome(before.direction, pnl=-1.0)
        after = engine.predict(df)
        self.assertIsNotNone(after)
        self.assertEqual(after.direction, before.direction)
        self.assertLessEqual(after.confidence, before.confidence)


if __name__ == "__main__":
    unittest.main()
