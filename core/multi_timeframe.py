"""
Multi-timeframe analysis module.

Analyses three timeframes (5 m, 1 h, 4 h) and builds a consensus
signal.  A higher-timeframe confirmation significantly boosts
signal confidence.
"""

import logging
from dataclasses import dataclass

import pandas as pd

from core.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger("trading_bot.multi_timeframe")

TIMEFRAMES = ["5m", "1h", "4h"]

# Weight given to each timeframe in the final score (higher TF = more weight)
TF_WEIGHTS: dict[str, float] = {
    "5m": 0.2,
    "1h": 0.35,
    "4h": 0.45,
}


@dataclass
class TimeframeSignal:
    """Analysis result for a single timeframe."""

    timeframe: str
    trend: str
    rsi: float | None
    macd_bullish: bool
    ema_bullish: bool
    bb_position: str   # LOWER / MIDDLE / UPPER
    adx: float | None
    direction: str     # BUY / SELL / NEUTRAL


@dataclass
class MTFResult:
    """Combined multi-timeframe analysis result."""

    direction: str           # BUY / SELL / NEUTRAL
    confidence: float        # 0-1
    tf_signals: list[TimeframeSignal]
    alignment: str           # ALIGNED / PARTIAL / CONFLICTING
    dominant_trend: str      # UPTREND / DOWNTREND / SIDEWAYS


class MultiTimeframeAnalyzer:
    """Analyse multiple timeframes and combine into a single verdict."""

    def __init__(self) -> None:
        self.ta = TechnicalAnalyzer()

    def analyse_timeframe(self, df: pd.DataFrame, timeframe: str) -> TimeframeSignal | None:
        """Run technical analysis on a single timeframe DataFrame."""
        if df.empty or len(df) < 50:
            logger.warning("Not enough data for %s analysis (%d rows)", timeframe, len(df))
            return None

        result = self.ta.analyse(df)
        if not result:
            return None

        rsi = result.get("rsi")
        macd_line = result.get("macd_line", 0)
        macd_signal_val = result.get("macd_signal", 0)
        ema_fast = result.get("ema_fast", 0)
        ema_medium = result.get("ema_medium", 0)
        ema_slow = result.get("ema_slow", 0)
        close = result.get("close", 0)
        bb_lower = result.get("bb_lower", 0)
        bb_upper = result.get("bb_upper", 0)
        adx = result.get("adx")
        trend = result.get("trend", "SIDEWAYS")

        macd_bullish = (macd_line or 0) > (macd_signal_val or 0)
        ema_bullish = (ema_fast > ema_medium > ema_slow) if all([ema_fast, ema_medium, ema_slow]) else False

        # BB position
        if close and bb_lower and close <= bb_lower:
            bb_pos = "LOWER"
        elif close and bb_upper and close >= bb_upper:
            bb_pos = "UPPER"
        else:
            bb_pos = "MIDDLE"

        # Direction vote
        buy_votes = 0
        sell_votes = 0

        if rsi is not None:
            if rsi < 30:
                buy_votes += 1
            elif rsi > 70:
                sell_votes += 1

        if macd_bullish:
            buy_votes += 1
        else:
            sell_votes += 1

        if ema_bullish:
            buy_votes += 1
        elif ema_fast and ema_medium and ema_slow and ema_fast < ema_medium < ema_slow:
            sell_votes += 1

        if buy_votes > sell_votes:
            direction = "BUY"
        elif sell_votes > buy_votes:
            direction = "SELL"
        else:
            direction = "NEUTRAL"

        return TimeframeSignal(
            timeframe=timeframe,
            trend=trend,
            rsi=rsi,
            macd_bullish=macd_bullish,
            ema_bullish=ema_bullish,
            bb_position=bb_pos,
            adx=adx,
            direction=direction,
        )

    def analyse(self, dataframes: dict[str, pd.DataFrame]) -> MTFResult | None:
        """Analyse all timeframes and combine into a single result.

        Parameters
        ----------
        dataframes : dict
            Mapping of timeframe label (e.g. ``"5m"``) to OHLCV DataFrame.
        """
        tf_signals: list[TimeframeSignal] = []

        for tf in TIMEFRAMES:
            df = dataframes.get(tf)
            if df is None or df.empty:
                continue
            sig = self.analyse_timeframe(df, tf)
            if sig:
                tf_signals.append(sig)

        if not tf_signals:
            return None

        # Weighted voting
        buy_score = 0.0
        sell_score = 0.0

        for sig in tf_signals:
            weight = TF_WEIGHTS.get(sig.timeframe, 0.33)
            if sig.direction == "BUY":
                buy_score += weight
            elif sig.direction == "SELL":
                sell_score += weight

        total_weight = sum(TF_WEIGHTS.get(s.timeframe, 0.33) for s in tf_signals)
        if total_weight == 0:
            return None

        if buy_score > sell_score:
            direction = "BUY"
            raw_conf = buy_score / total_weight
        elif sell_score > buy_score:
            direction = "SELL"
            raw_conf = sell_score / total_weight
        else:
            direction = "NEUTRAL"
            raw_conf = 0.5

        # Alignment check
        directions = {s.direction for s in tf_signals}
        if len(directions) == 1 and "NEUTRAL" not in directions:
            alignment = "ALIGNED"
            raw_conf = min(raw_conf * 1.15, 1.0)  # bonus for full alignment
        elif direction != "NEUTRAL" and direction in directions:
            alignment = "PARTIAL"
        else:
            alignment = "CONFLICTING"
            raw_conf *= 0.7  # penalty

        # Dominant trend from highest timeframe
        dominant_trend = "SIDEWAYS"
        for sig in reversed(tf_signals):
            if sig.trend in ("UPTREND", "DOWNTREND"):
                dominant_trend = sig.trend
                break

        result = MTFResult(
            direction=direction,
            confidence=round(raw_conf, 4),
            tf_signals=tf_signals,
            alignment=alignment,
            dominant_trend=dominant_trend,
        )

        logger.info(
            "MTF result: %s (conf=%.1f%%, align=%s, trend=%s)",
            result.direction,
            result.confidence * 100,
            result.alignment,
            result.dominant_trend,
        )
        return result
