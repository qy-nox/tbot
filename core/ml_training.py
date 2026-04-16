"""ML training and walk-forward backtesting helpers."""

from __future__ import annotations

import pandas as pd

from core.advanced_ml_engine import AdvancedMLEngine


class MLTrainer:
    def __init__(self) -> None:
        self.engine = AdvancedMLEngine()

    def train_models(self, df: pd.DataFrame) -> dict:
        return self.engine.train(df)

    def backtest(self, df: pd.DataFrame, window: int = 300) -> dict:
        if len(df) < window + 10:
            return {"samples": 0, "hit_rate": 0.0}

        hits = 0
        samples = 0
        for i in range(window, len(df) - 1):
            pred = self.engine.predict(df.iloc[: i + 1])
            if not pred:
                continue
            move_up = df["close"].iloc[i + 1] >= df["close"].iloc[i]
            if (pred.direction == "BUY" and move_up) or (pred.direction == "SELL" and not move_up):
                hits += 1
            samples += 1
        return {"samples": samples, "hit_rate": (hits / samples) if samples else 0.0}
