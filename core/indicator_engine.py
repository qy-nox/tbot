"""Professional indicator engine with broad indicator coverage."""

from __future__ import annotations

import numpy as np
import pandas as pd

from core.technical_analyzer import TechnicalAnalyzer


class IndicatorEngine:
    def __init__(self) -> None:
        self.base = TechnicalAnalyzer()

    def compute_all(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}

        base = self.base.analyse(df)
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"] if "volume" in df else pd.Series(np.zeros(len(df)), index=df.index)

        stochastic_k, stochastic_d = self._stochastic(close, high, low)
        mfi = self._mfi(high, low, close, volume)
        williams_r = self._williams_r(high, low, close)
        cci = self._cci(high, low, close)
        roc = self._roc(close)
        vwma = self._vwma(close, volume)
        ichimoku = self._ichimoku(high, low, close)
        divergence = self._rsi_divergence(close, self.base.compute_rsi(df))

        base.update(
            {
                "stochastic_k": float(stochastic_k.iloc[-1]) if not stochastic_k.empty else None,
                "stochastic_d": float(stochastic_d.iloc[-1]) if not stochastic_d.empty else None,
                "mfi": float(mfi.iloc[-1]) if not mfi.empty else None,
                "williams_r": float(williams_r.iloc[-1]) if not williams_r.empty else None,
                "cci": float(cci.iloc[-1]) if not cci.empty else None,
                "roc": float(roc.iloc[-1]) if not roc.empty else None,
                "vwma": float(vwma.iloc[-1]) if not vwma.empty else None,
                "ichimoku": ichimoku,
                "rsi_divergence": divergence,
            }
        )
        return base

    @staticmethod
    def _stochastic(close: pd.Series, high: pd.Series, low: pd.Series, period: int = 14) -> tuple[pd.Series, pd.Series]:
        lowest = low.rolling(period).min()
        highest = high.rolling(period).max()
        k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
        d = k.rolling(3).mean()
        return k, d

    @staticmethod
    def _vwma(close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        return (close * volume).rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)

    @staticmethod
    def _mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        typical = (high + low + close) / 3
        money_flow = typical * volume
        direction = typical.diff()
        positive = money_flow.where(direction > 0, 0.0)
        negative = money_flow.where(direction < 0, 0.0).abs()
        pos_sum = positive.rolling(period).sum()
        neg_sum = negative.rolling(period).sum()
        ratio = pos_sum / neg_sum.replace(0, np.nan)
        return 100 - (100 / (1 + ratio))

    @staticmethod
    def _williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        highest = high.rolling(period).max()
        lowest = low.rolling(period).min()
        return -100 * (highest - close) / (highest - lowest).replace(0, np.nan)

    @staticmethod
    def _cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        tp = (high + low + close) / 3
        sma = tp.rolling(period).mean()
        mad = (tp - sma).abs().rolling(period).mean()
        return (tp - sma) / (0.015 * mad.replace(0, np.nan))

    @staticmethod
    def _roc(close: pd.Series, period: int = 12) -> pd.Series:
        return ((close / close.shift(period)) - 1.0) * 100

    @staticmethod
    def _ichimoku(high: pd.Series, low: pd.Series, close: pd.Series) -> dict[str, float | None]:
        conversion = (high.rolling(9).max() + low.rolling(9).min()) / 2
        base = (high.rolling(26).max() + low.rolling(26).min()) / 2
        span_a = ((conversion + base) / 2).shift(26)
        span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        lagging = close.shift(-26)
        return {
            "conversion": float(conversion.iloc[-1]) if not conversion.empty and pd.notna(conversion.iloc[-1]) else None,
            "base": float(base.iloc[-1]) if not base.empty and pd.notna(base.iloc[-1]) else None,
            "span_a": float(span_a.iloc[-1]) if not span_a.empty and pd.notna(span_a.iloc[-1]) else None,
            "span_b": float(span_b.iloc[-1]) if not span_b.empty and pd.notna(span_b.iloc[-1]) else None,
            "lagging": float(lagging.iloc[-1]) if not lagging.empty and pd.notna(lagging.iloc[-1]) else None,
        }

    @staticmethod
    def _rsi_divergence(close: pd.Series, rsi: pd.Series, lookback: int = 20) -> str:
        if len(close) < lookback or len(rsi.dropna()) < lookback:
            return "NONE"
        c = close.tail(lookback)
        r = rsi.tail(lookback)
        if c.iloc[-1] < c.iloc[0] and r.iloc[-1] > r.iloc[0]:
            return "BULLISH"
        if c.iloc[-1] > c.iloc[0] and r.iloc[-1] < r.iloc[0]:
            return "BEARISH"
        return "NONE"
