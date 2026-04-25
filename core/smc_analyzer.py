"""
Smart Money Concepts (SMC) analyzer.

Detects institutional price action patterns:
  - Order Blocks (OB)
  - Break of Structure (BOS)
  - Change of Character (CHoCH)
  - Fair Value Gaps (FVG)
  - Liquidity levels (swing highs/lows)
  - Mitigation events

These concepts are already partially embedded in TechnicalAnalyzer.
This module provides a dedicated, higher-level SMC interface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

logger = logging.getLogger("trading_bot.smc_analyzer")


@dataclass
class OrderBlock:
    """A single order block zone."""

    kind: str  # "bullish" | "bearish"
    low: float
    high: float
    open: float
    close: float
    index: int
    mitigated: bool = False


@dataclass
class FairValueGap:
    """A fair-value gap (imbalance) between three consecutive candles."""

    kind: str  # "bullish" | "bearish"
    low: float
    high: float
    index: int
    filled: bool = False


@dataclass
class SMCResult:
    """Aggregated SMC analysis output."""

    trend: str  # "BULLISH" | "BEARISH" | "NEUTRAL"
    bos: bool  # Break of Structure detected
    choch: bool  # Change of Character detected
    order_blocks: list[OrderBlock] = field(default_factory=list)
    fair_value_gaps: list[FairValueGap] = field(default_factory=list)
    swing_highs: list[float] = field(default_factory=list)
    swing_lows: list[float] = field(default_factory=list)
    nearest_ob: OrderBlock | None = None
    signal_bias: str = "NEUTRAL"  # "LONG" | "SHORT" | "NEUTRAL"
    confidence: float = 0.0
    reasons: list[str] = field(default_factory=list)


class SMCAnalyzer:
    """Smart Money Concepts price-action analyzer."""

    def __init__(
        self,
        swing_lookback: int = 5,
        fvg_min_pct: float = 0.001,
        ob_min_body_ratio: float = 1.2,
    ) -> None:
        """
        Parameters
        ----------
        swing_lookback:
            Number of bars to look back/forward when identifying swing points.
        fvg_min_pct:
            Minimum gap size as a fraction of price to register as a FVG.
        ob_min_body_ratio:
            Minimum body-to-average-body ratio to qualify as an order block.
        """
        self.swing_lookback = swing_lookback
        self.fvg_min_pct = fvg_min_pct
        self.ob_min_body_ratio = ob_min_body_ratio

    # ── Public API ─────────────────────────────────────────────────────

    def analyse(self, df: pd.DataFrame) -> SMCResult:
        """Run the full SMC suite and return an :class:`SMCResult`."""
        df = self._normalise(df)
        if df.empty or len(df) < self.swing_lookback * 2 + 2:
            logger.warning("SMCAnalyzer: insufficient data (%d rows)", len(df))
            return SMCResult(trend="NEUTRAL", bos=False, choch=False)

        swing_highs, swing_lows = self._detect_swings(df)
        trend = self._determine_trend(df, swing_highs, swing_lows)
        bos, choch = self._detect_bos_choch(df, swing_highs, swing_lows, trend)
        order_blocks = self._detect_order_blocks(df)
        fvgs = self._detect_fair_value_gaps(df)

        # Mark mitigated order blocks (price has re-entered the zone)
        current_price = float(df["close"].iloc[-1])
        for ob in order_blocks:
            if ob.low <= current_price <= ob.high:
                ob.mitigated = True

        # Find nearest order block to current price
        nearest_ob = self._nearest_order_block(order_blocks, current_price)

        # Mark filled FVGs
        for fvg in fvgs:
            body_idx = min(fvg.index + 1, len(df) - 1)
            subsequent = df["close"].iloc[body_idx:]
            if fvg.kind == "bullish":
                fvg.filled = bool((subsequent <= fvg.high).any())
            else:
                fvg.filled = bool((subsequent >= fvg.low).any())

        signal_bias, confidence, reasons = self._compute_bias(
            trend, bos, choch, order_blocks, fvgs, nearest_ob, current_price
        )

        return SMCResult(
            trend=trend,
            bos=bos,
            choch=choch,
            order_blocks=order_blocks,
            fair_value_gaps=fvgs,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
            nearest_ob=nearest_ob,
            signal_bias=signal_bias,
            confidence=confidence,
            reasons=reasons,
        )

    # ── Swing detection ────────────────────────────────────────────────

    def _detect_swings(
        self, df: pd.DataFrame
    ) -> tuple[list[float], list[float]]:
        n = self.swing_lookback
        highs: list[float] = []
        lows: list[float] = []

        for i in range(n, len(df) - n):
            window_high = df["high"].iloc[i - n : i + n + 1]
            window_low = df["low"].iloc[i - n : i + n + 1]
            if df["high"].iloc[i] == window_high.max():
                highs.append(float(df["high"].iloc[i]))
            if df["low"].iloc[i] == window_low.min():
                lows.append(float(df["low"].iloc[i]))

        return highs, lows

    # ── Trend ──────────────────────────────────────────────────────────

    @staticmethod
    def _determine_trend(
        df: pd.DataFrame,
        swing_highs: list[float],
        swing_lows: list[float],
    ) -> str:
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            hh = swing_highs[-1] > swing_highs[-2]
            hl = swing_lows[-1] > swing_lows[-2]
            lh = swing_highs[-1] < swing_highs[-2]
            ll = swing_lows[-1] < swing_lows[-2]
            if hh and hl:
                return "BULLISH"
            if lh and ll:
                return "BEARISH"
        # Fallback: EMA slope
        close = df["close"]
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()
        if ema20.iloc[-1] > ema50.iloc[-1]:
            return "BULLISH"
        if ema20.iloc[-1] < ema50.iloc[-1]:
            return "BEARISH"
        return "NEUTRAL"

    # ── BOS / CHoCH ────────────────────────────────────────────────────

    @staticmethod
    def _detect_bos_choch(
        df: pd.DataFrame,
        swing_highs: list[float],
        swing_lows: list[float],
        trend: str,
    ) -> tuple[bool, bool]:
        """Return (bos, choch) booleans."""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return False, False

        last_close = float(df["close"].iloc[-1])
        prev_high = swing_highs[-2]
        prev_low = swing_lows[-2]

        bos = False
        choch = False

        if trend == "BULLISH":
            if last_close > prev_high:
                bos = True
            elif last_close < prev_low:
                choch = True
        elif trend == "BEARISH":
            if last_close < prev_low:
                bos = True
            elif last_close > prev_high:
                choch = True

        return bos, choch

    # ── Order blocks ───────────────────────────────────────────────────

    def _detect_order_blocks(self, df: pd.DataFrame) -> list[OrderBlock]:
        obs: list[OrderBlock] = []
        body = (df["close"] - df["open"]).abs()
        avg_body = body.rolling(20).mean()

        for i in range(1, len(df) - 2):
            if pd.isna(avg_body.iloc[i]) or avg_body.iloc[i] < 1e-10:
                continue

            ratio = body.iloc[i] / avg_body.iloc[i]
            if ratio < self.ob_min_body_ratio:
                continue

            move_pct = (df["close"].iloc[i + 1] - df["close"].iloc[i]) / df["close"].iloc[i]

            # Bullish OB: bearish candle before a strong up-move
            if df["close"].iloc[i] < df["open"].iloc[i] and move_pct > 0.005:
                obs.append(
                    OrderBlock(
                        kind="bullish",
                        low=float(df["low"].iloc[i]),
                        high=float(df["high"].iloc[i]),
                        open=float(df["open"].iloc[i]),
                        close=float(df["close"].iloc[i]),
                        index=i,
                    )
                )

            # Bearish OB: bullish candle before a strong down-move
            if df["close"].iloc[i] > df["open"].iloc[i] and move_pct < -0.005:
                obs.append(
                    OrderBlock(
                        kind="bearish",
                        low=float(df["low"].iloc[i]),
                        high=float(df["high"].iloc[i]),
                        open=float(df["open"].iloc[i]),
                        close=float(df["close"].iloc[i]),
                        index=i,
                    )
                )

        return obs

    # ── Fair Value Gaps ────────────────────────────────────────────────

    def _detect_fair_value_gaps(self, df: pd.DataFrame) -> list[FairValueGap]:
        fvgs: list[FairValueGap] = []

        for i in range(1, len(df) - 1):
            candle1_high = float(df["high"].iloc[i - 1])
            candle1_low = float(df["low"].iloc[i - 1])
            candle3_high = float(df["high"].iloc[i + 1])
            candle3_low = float(df["low"].iloc[i + 1])

            mid_price = float(df["close"].iloc[i])
            if mid_price == 0:
                continue

            # Bullish FVG: gap between candle1 high and candle3 low
            if candle3_low > candle1_high:
                gap_pct = (candle3_low - candle1_high) / mid_price
                if gap_pct >= self.fvg_min_pct:
                    fvgs.append(
                        FairValueGap(
                            kind="bullish",
                            low=candle1_high,
                            high=candle3_low,
                            index=i,
                        )
                    )

            # Bearish FVG: gap between candle1 low and candle3 high
            if candle1_low > candle3_high:
                gap_pct = (candle1_low - candle3_high) / mid_price
                if gap_pct >= self.fvg_min_pct:
                    fvgs.append(
                        FairValueGap(
                            kind="bearish",
                            low=candle3_high,
                            high=candle1_low,
                            index=i,
                        )
                    )

        return fvgs

    # ── Signal bias ────────────────────────────────────────────────────

    @staticmethod
    def _nearest_order_block(
        obs: list[OrderBlock], price: float
    ) -> OrderBlock | None:
        """Return the unmitigated order block closest to *price*."""
        candidates = [ob for ob in obs if not ob.mitigated]
        if not candidates:
            return None
        return min(candidates, key=lambda ob: abs((ob.low + ob.high) / 2 - price))

    @staticmethod
    def _compute_bias(
        trend: str,
        bos: bool,
        choch: bool,
        obs: list[OrderBlock],
        fvgs: list[FairValueGap],
        nearest_ob: OrderBlock | None,
        current_price: float,
    ) -> tuple[str, float, list[str]]:
        score = 0.0
        reasons: list[str] = []

        if trend == "BULLISH":
            score += 1.0
            reasons.append("SMC bullish structure")
        elif trend == "BEARISH":
            score -= 1.0
            reasons.append("SMC bearish structure")

        if bos:
            if trend == "BULLISH":
                score += 0.5
                reasons.append("BOS continuation (bullish)")
            else:
                score -= 0.5
                reasons.append("BOS continuation (bearish)")

        if choch:
            if trend == "BULLISH":
                score -= 0.75
                reasons.append("CHoCH – potential reversal bearish")
            else:
                score += 0.75
                reasons.append("CHoCH – potential reversal bullish")

        if nearest_ob is not None:
            if nearest_ob.kind == "bullish" and nearest_ob.mitigated:
                score += 0.5
                reasons.append("Price at bullish OB (mitigation)")
            elif nearest_ob.kind == "bearish" and nearest_ob.mitigated:
                score -= 0.5
                reasons.append("Price at bearish OB (mitigation)")

        unfilled_bullish_fvg = sum(1 for f in fvgs if f.kind == "bullish" and not f.filled)
        unfilled_bearish_fvg = sum(1 for f in fvgs if f.kind == "bearish" and not f.filled)
        if unfilled_bullish_fvg > unfilled_bearish_fvg:
            score += 0.25
        elif unfilled_bearish_fvg > unfilled_bullish_fvg:
            score -= 0.25

        if score > 0.5:
            bias = "LONG"
        elif score < -0.5:
            bias = "SHORT"
        else:
            bias = "NEUTRAL"

        confidence = min(abs(score) / 2.5, 1.0)
        return bias, round(confidence, 3), reasons

    # ── Utility ────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure lowercase OHLCV column names and reset integer index."""
        df = df.copy()
        df.columns = [str(c).lower() for c in df.columns]
        required = {"open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns):
            missing = required - set(df.columns)
            logger.warning("SMCAnalyzer: missing columns %s", missing)
            return pd.DataFrame()
        df = df.reset_index(drop=True)
        # Drop rows with NaN in OHLCV
        df = df.dropna(subset=list(required))
        return df
