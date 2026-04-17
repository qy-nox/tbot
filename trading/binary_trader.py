"""Binary options signal helper with fixed expiry buckets."""

from __future__ import annotations


class BinaryTrader:
    EXPIRIES = {"5m": 300, "15m": 900, "1h": 3600}

    def generate_signal(self, *, pair: str, timeframe: str, rsi: float, ema20: float, ema50: float, close: float, bb_upper: float, bb_lower: float) -> dict | None:
        direction = None
        reasons: list[str] = []

        if rsi < 30 and close <= bb_lower and ema20 >= ema50:
            direction = "CALL"
            reasons = ["RSI oversold", "Lower band touch", "EMA bullish"]
        elif rsi > 70 and close >= bb_upper and ema20 <= ema50:
            direction = "PUT"
            reasons = ["RSI overbought", "Upper band touch", "EMA bearish"]

        if direction is None:
            return None

        return {
            "pair": pair,
            "timeframe": timeframe,
            "direction": direction,
            "expiry_seconds": self.EXPIRIES.get(timeframe, 300),
            "confidence": 0.75,
            "reasons": reasons,
        }
