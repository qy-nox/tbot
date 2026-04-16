"""Pattern recognition utilities (fractal/divergence/order-block proxies)."""

from __future__ import annotations

import pandas as pd


class PatternRecognition:
    def detect(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {"fractal": None, "divergence": None, "order_blocks": []}
        close = df["close"]
        fractal = "bullish" if close.iloc[-1] > close.iloc[-5:].mean() else "bearish"
        divergence = "none"
        return {"fractal": fractal, "divergence": divergence, "order_blocks": []}
