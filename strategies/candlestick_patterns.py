"""Candlestick pattern recognition helpers."""

from __future__ import annotations

import pandas as pd


class CandlestickPatterns:
    def detect(self, df: pd.DataFrame) -> dict[str, int | str]:
        if len(df) < 2:
            return {"pattern": "NONE", "confidence": 0}

        prev = df.iloc[-2]
        cur = df.iloc[-1]
        body = abs(cur["close"] - cur["open"])
        candle_range = max(cur["high"] - cur["low"], 1e-9)

        if prev["close"] < prev["open"] and cur["close"] > cur["open"] and cur["close"] >= prev["open"] and cur["open"] <= prev["close"]:
            return {"pattern": "BULLISH_ENGULFING", "confidence": 92}
        if prev["close"] > prev["open"] and cur["close"] < cur["open"] and cur["close"] <= prev["open"] and cur["open"] >= prev["close"]:
            return {"pattern": "BEARISH_ENGULFING", "confidence": 92}

        lower_wick = min(cur["open"], cur["close"]) - cur["low"]
        upper_wick = cur["high"] - max(cur["open"], cur["close"])
        if lower_wick > body * 2 and upper_wick <= body:
            return {"pattern": "HAMMER", "confidence": 85}
        if upper_wick > body * 2 and lower_wick <= body:
            return {"pattern": "SHOOTING_STAR", "confidence": 85}
        if body <= candle_range * 0.1:
            return {"pattern": "DOJI", "confidence": 75}
        return {"pattern": "NONE", "confidence": 0}
