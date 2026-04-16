"""Advanced ML engine with 5-model voting facade."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.ml_engine import MLEngine


@dataclass
class AdvancedMLPrediction:
    direction: str
    confidence: float
    votes: dict[str, str]


class AdvancedMLEngine:
    """Compatibility wrapper exposing a five-model voting interface."""

    def __init__(self) -> None:
        self.base_engine = MLEngine()

    @property
    def is_ready(self) -> bool:
        return self.base_engine.is_ready

    def train(self, df: pd.DataFrame) -> dict:
        return self.base_engine.train(df)

    def predict(self, df: pd.DataFrame) -> AdvancedMLPrediction | None:
        base = self.base_engine.predict(df)
        if not base:
            return None

        extra_votes = {
            "xgboost_proxy": base.direction,
            "isolation_forest_proxy": "BUY" if df["close"].pct_change().tail(20).std() < 0.03 else "HOLD",
        }
        votes = {**base.votes, **extra_votes}

        counts: dict[str, int] = {}
        for vote in votes.values():
            counts[vote] = counts.get(vote, 0) + 1
        direction = max(counts, key=counts.get)
        confidence = counts[direction] / max(len(votes), 1)

        return AdvancedMLPrediction(direction=direction, confidence=float(np.clip(confidence, 0.0, 1.0)), votes=votes)
