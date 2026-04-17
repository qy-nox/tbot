"""Price action analysis helpers for breakout, pullback and structure detection."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class EntryZone:
    minimum: float
    maximum: float


class PriceActionAnalyzer:
    def detect_support_resistance(self, df: pd.DataFrame, window: int = 5) -> dict[str, list[float]]:
        if df.empty or len(df) < window * 2 + 1:
            return {"supports": [], "resistances": []}

        supports: list[float] = []
        resistances: list[float] = []
        for i in range(window, len(df) - window):
            low_slice = df["low"].iloc[i - window : i + window + 1]
            high_slice = df["high"].iloc[i - window : i + window + 1]
            if df["low"].iloc[i] == low_slice.min():
                supports.append(float(df["low"].iloc[i]))
            if df["high"].iloc[i] == high_slice.max():
                resistances.append(float(df["high"].iloc[i]))

        return {
            "supports": self._dedupe_levels(supports),
            "resistances": self._dedupe_levels(resistances),
        }

    def identify_trend(self, df: pd.DataFrame, lookback: int = 20) -> str:
        if df.empty or len(df) < lookback:
            return "SIDEWAYS"
        recent = df.tail(lookback)
        high_slope = recent["high"].iloc[-1] - recent["high"].iloc[0]
        low_slope = recent["low"].iloc[-1] - recent["low"].iloc[0]
        if high_slope > 0 and low_slope > 0:
            return "UPTREND"
        if high_slope < 0 and low_slope < 0:
            return "DOWNTREND"
        return "SIDEWAYS"

    def detect_candlestick_pattern(self, df: pd.DataFrame) -> str:
        if len(df) < 2:
            return "NONE"
        prev = df.iloc[-2]
        last = df.iloc[-1]

        last_body = abs(last["close"] - last["open"])
        candle_range = max(float(last["high"] - last["low"]), 1e-9)

        bullish_engulfing = (
            prev["close"] < prev["open"]
            and last["close"] > last["open"]
            and last["open"] <= prev["close"]
            and last["close"] >= prev["open"]
        )
        bearish_engulfing = (
            prev["close"] > prev["open"]
            and last["close"] < last["open"]
            and last["open"] >= prev["close"]
            and last["close"] <= prev["open"]
        )

        lower_wick = min(last["open"], last["close"]) - last["low"]
        upper_wick = last["high"] - max(last["open"], last["close"])

        if bullish_engulfing:
            return "BULLISH_ENGULFING"
        if bearish_engulfing:
            return "BEARISH_ENGULFING"
        if lower_wick > last_body * 2 and upper_wick <= last_body:
            return "HAMMER"
        if upper_wick > last_body * 2 and lower_wick <= last_body:
            return "SHOOTING_STAR"
        if last_body <= candle_range * 0.1:
            return "DOJI"
        return "NONE"

    def market_structure(self, df: pd.DataFrame, lookback: int = 5) -> str:
        if len(df) < lookback + 2:
            return "UNKNOWN"
        highs = df["high"].tail(lookback + 1).reset_index(drop=True)
        lows = df["low"].tail(lookback + 1).reset_index(drop=True)

        higher_highs = all(highs.iloc[i] >= highs.iloc[i - 1] for i in range(1, len(highs)))
        higher_lows = all(lows.iloc[i] >= lows.iloc[i - 1] for i in range(1, len(lows)))
        lower_highs = all(highs.iloc[i] <= highs.iloc[i - 1] for i in range(1, len(highs)))
        lower_lows = all(lows.iloc[i] <= lows.iloc[i - 1] for i in range(1, len(lows)))

        if higher_highs and higher_lows:
            return "HIGHER_HIGHS_HIGHER_LOWS"
        if lower_highs and lower_lows:
            return "LOWER_HIGHS_LOWER_LOWS"
        return "MIXED"

    @staticmethod
    def identify_entry_zone(price: float, tolerance_pct: float = 0.02) -> EntryZone:
        delta = price * tolerance_pct
        return EntryZone(minimum=round(price - delta, 8), maximum=round(price + delta, 8))

    def analyze(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}

        levels = self.detect_support_resistance(df)
        trend = self.identify_trend(df)
        pattern = self.detect_candlestick_pattern(df)
        structure = self.market_structure(df)
        close = float(df["close"].iloc[-1])
        volume_avg = float(df["volume"].tail(20).mean()) if "volume" in df and not df["volume"].empty else 0.0
        volume_now = float(df["volume"].iloc[-1]) if "volume" in df else 0.0

        breakout = any(close > level for level in levels["resistances"][-3:]) if levels["resistances"] else False
        pullback = trend == "UPTREND" and len(df) > 2 and float(df["close"].iloc[-2]) < float(df["close"].iloc[-3])

        zone = self.identify_entry_zone(close)
        return {
            "trend": trend,
            "pattern": pattern,
            "market_structure": structure,
            "support_resistance": levels,
            "breakout": breakout,
            "pullback": pullback,
            "volume_profile": {
                "current": volume_now,
                "average_20": volume_avg,
                "above_average": volume_now >= volume_avg if volume_avg else False,
            },
            "entry_zone": {"min": zone.minimum, "max": zone.maximum},
        }

    @staticmethod
    def _dedupe_levels(levels: list[float], tolerance: float = 0.005) -> list[float]:
        if not levels:
            return []
        deduped: list[float] = []
        for level in sorted(set(levels)):
            if not deduped or abs(level - deduped[-1]) / max(deduped[-1], 1e-9) > tolerance:
                deduped.append(level)
        return deduped
