"""Lightweight advanced ML ensemble interface for direction probability."""

from __future__ import annotations

import numpy as np
import pandas as pd


class AdvancedMLEngine:
    """Fallback-safe ensemble model interface."""

    def predict_direction_probability(self, df: pd.DataFrame, lookback: int = 200) -> dict[str, float | str]:
        if df.empty:
            return {"direction": "HOLD", "probability": 0.5, "confidence": 0.0}

        series = df["close"].tail(lookback)
        if len(series) < 2:
            return {"direction": "HOLD", "probability": 0.5, "confidence": 0.0}

        momentum = float((series.iloc[-1] - series.iloc[0]) / max(series.iloc[0], 1e-9))
        volatility = float(series.pct_change().dropna().std() or 0.0)

        raw_score = 0.5 + momentum - min(volatility, 0.2) * 0.5
        probability = float(np.clip(raw_score, 0.0, 1.0))
        if probability > 0.55:
            direction = "BUY"
        elif probability < 0.45:
            direction = "SELL"
        else:
            direction = "HOLD"

        confidence = float(abs(probability - 0.5) * 2)
        return {"direction": direction, "probability": round(probability, 4), "confidence": round(confidence, 4)}
