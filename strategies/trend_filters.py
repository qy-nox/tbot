"""Trend, momentum, volatility and volume filtering utilities."""

from __future__ import annotations


class TrendFilters:
    def detect_trend(self, ema20: float, ema50: float, ema200: float) -> str:
        if ema20 > ema50 > ema200:
            return "UPTREND"
        if ema20 < ema50 < ema200:
            return "DOWNTREND"
        return "SIDEWAYS"

    def is_trending_market(self, adx: float) -> bool:
        return adx >= 25

    def momentum_ok(self, direction: str, macd_line: float) -> bool:
        if direction == "BUY":
            return macd_line >= 0
        if direction == "SELL":
            return macd_line <= 0
        return False

    def volatility_ok(self, atr: float, atr_avg_200: float, min_ratio: float = 0.005) -> bool:
        if atr_avg_200 <= 0:
            return False
        return (atr / atr_avg_200) >= min_ratio

    def volume_ok(self, current_volume: float, avg_volume_20: float) -> bool:
        return avg_volume_20 > 0 and current_volume >= avg_volume_20

    def allow_signal(self, direction: str, trend: str, adx: float, macd_line: float, atr: float, atr_avg_200: float, current_volume: float, avg_volume_20: float) -> tuple[bool, str]:
        if trend == "SIDEWAYS":
            return False, "sideways market"
        if direction == "BUY" and trend != "UPTREND":
            return False, "buy against trend"
        if direction == "SELL" and trend != "DOWNTREND":
            return False, "sell against trend"
        if adx < 20:
            return False, "choppy market (low ADX)"
        if not self.momentum_ok(direction, macd_line):
            return False, "momentum conflict"
        if not self.volatility_ok(atr, atr_avg_200):
            return False, "low volatility"
        if not self.volume_ok(current_volume, avg_volume_20):
            return False, "low volume"
        return True, "ok"
