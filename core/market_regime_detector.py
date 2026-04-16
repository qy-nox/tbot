"""Market regime detection utilities."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketRegimeResult:
    regime: str
    trend_strength: float
    volatility: float


class MarketRegimeDetector:
    """Classify market state into TRENDING, RANGING, or VOLATILE."""

    def detect(self, df: pd.DataFrame) -> MarketRegimeResult:
        if len(df) < 30:
            return MarketRegimeResult(regime="RANGING", trend_strength=0.0, volatility=0.0)

        close = df["close"]
        returns = close.pct_change().dropna()
        volatility = float(returns.tail(30).std()) if not returns.empty else 0.0

        ema_fast = close.ewm(span=10, adjust=False).mean()
        ema_slow = close.ewm(span=30, adjust=False).mean()
        trend_strength = float(abs((ema_fast.iloc[-1] - ema_slow.iloc[-1]) / max(close.iloc[-1], 1e-9)))

        if volatility >= 0.03:
            regime = "VOLATILE"
        elif trend_strength >= 0.015:
            regime = "TRENDING"
        else:
            regime = "RANGING"

        return MarketRegimeResult(
            regime=regime,
            trend_strength=round(trend_strength, 6),
            volatility=round(volatility, 6),
        )
