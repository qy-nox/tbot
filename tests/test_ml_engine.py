import unittest

import pandas as pd

from core.advanced_ml_engine import AdvancedMLEngine


class TestAdvancedMLEngine(unittest.TestCase):
    def test_engine_exposes_train_predict(self):
        engine = AdvancedMLEngine()
        self.assertTrue(hasattr(engine, "train"))
        self.assertTrue(hasattr(engine, "predict"))


if __name__ == "__main__":
    unittest.main()
