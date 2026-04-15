"""
Binary options signal generator.

Produces short-duration CALL / PUT signals suitable for binary-options
platforms (IQ Option, Pocket Option, etc.).

Key differences from crypto spot/futures signals:
- Very short timeframes (30 s – 5 min candles)
- Fixed-duration trades (expiry instead of TP/SL)
- Direction is CALL (up) or PUT (down)
- Confidence threshold is higher (≥ 75%) for better win rates
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from config.settings import Settings
from core.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger("trading_bot.binary_strategy")


@dataclass
class BinarySignal:
    """Represents a binary-options trading signal."""

    timestamp: datetime
    pair: str
    direction: str       # CALL / PUT
    entry_price: float
    expiry_seconds: int  # Duration in seconds (e.g. 60, 180, 300)
    confidence: float    # 0-1
    strength: str        # STRONG / MODERATE / WEAK
    reasons: list[str]
    strategy_name: str


class BinaryStrategyEngine:
    """Generate binary-option CALL/PUT signals from short-term indicators."""

    # Default binary-specific settings
    DEFAULT_EXPIRY = 300       # 5 minutes
    MIN_CONFIDENCE = 0.70      # 70 % minimum to emit a signal
    FAST_EMA = 5
    MEDIUM_EMA = 10
    SLOW_EMA = 20

    def __init__(self, expiry: int | None = None) -> None:
        self.analyzer = TechnicalAnalyzer()
        self.expiry = expiry or self.DEFAULT_EXPIRY

    # ── Main evaluation ─────────────────────────────────────────────────

    def evaluate(
        self,
        pair: str,
        df: pd.DataFrame,
    ) -> BinarySignal | None:
        """Evaluate short-term data and return a CALL/PUT signal or None."""
        if df.empty or len(df) < 30:
            logger.debug("%s: not enough data for binary analysis", pair)
            return None

        indicators = self._compute_fast_indicators(df)
        if not indicators:
            return None

        # Collect votes
        votes: list[str] = []
        reasons: list[str] = []

        rsi_vote, rsi_reason = self._rsi_signal(indicators)
        if rsi_vote:
            votes.append(rsi_vote)
            reasons.append(rsi_reason)

        ema_vote, ema_reason = self._ema_signal(indicators)
        if ema_vote:
            votes.append(ema_vote)
            reasons.append(ema_reason)

        macd_vote, macd_reason = self._macd_signal(indicators)
        if macd_vote:
            votes.append(macd_vote)
            reasons.append(macd_reason)

        bb_vote, bb_reason = self._bollinger_signal(indicators)
        if bb_vote:
            votes.append(bb_vote)
            reasons.append(bb_reason)

        momentum_vote, momentum_reason = self._momentum_signal(indicators)
        if momentum_vote:
            votes.append(momentum_vote)
            reasons.append(momentum_reason)

        # Consensus
        direction = self._consensus(votes)
        if direction == "NEUTRAL":
            logger.debug("%s: no binary consensus (%s)", pair, votes)
            return None

        # Confidence
        total = max(len(votes), 1)
        agree = sum(1 for v in votes if v == direction)
        confidence = agree / total

        if confidence < self.MIN_CONFIDENCE:
            logger.debug(
                "%s: binary confidence %.0f%% below threshold", pair, confidence * 100
            )
            return None

        # Strength classification
        if confidence >= 0.90:
            strength = "STRONG"
        elif confidence >= 0.75:
            strength = "MODERATE"
        else:
            strength = "WEAK"

        signal = BinarySignal(
            timestamp=datetime.now(timezone.utc),
            pair=pair,
            direction=direction,
            entry_price=float(df["close"].iloc[-1]),
            expiry_seconds=self.expiry,
            confidence=round(confidence, 4),
            strength=strength,
            reasons=reasons,
            strategy_name="binary_multi_indicator",
        )

        logger.info(
            "BINARY SIGNAL %s %s @ %.4f | conf=%.0f%% (%s) | expiry=%ds",
            direction, pair, signal.entry_price,
            confidence * 100, strength, self.expiry,
        )
        return signal

    # ── Fast indicator computation ──────────────────────────────────────

    def _compute_fast_indicators(self, df: pd.DataFrame) -> dict | None:
        """Compute a trimmed set of fast indicators for binary analysis."""
        try:
            close = df["close"]
            rsi = self.analyzer.compute_rsi(df)
            ema_fast = close.ewm(span=self.FAST_EMA, adjust=False).mean()
            ema_medium = close.ewm(span=self.MEDIUM_EMA, adjust=False).mean()
            ema_slow = close.ewm(span=self.SLOW_EMA, adjust=False).mean()
            macd_data = self.analyzer.compute_macd(df)
            bb = self.analyzer.compute_bollinger_bands(df)

            # Momentum: rate of change over last 3 candles
            roc_3 = close.pct_change(3)

            return {
                "close": float(close.iloc[-1]),
                "rsi": float(rsi.iloc[-1]) if not rsi.empty else None,
                "ema_fast": float(ema_fast.iloc[-1]),
                "ema_medium": float(ema_medium.iloc[-1]),
                "ema_slow": float(ema_slow.iloc[-1]),
                "macd_line": float(macd_data["macd_line"].iloc[-1]),
                "macd_signal": float(macd_data["signal_line"].iloc[-1]),
                "macd_hist": float(macd_data["histogram"].iloc[-1]),
                "bb_upper": float(bb["bb_upper"].iloc[-1]),
                "bb_lower": float(bb["bb_lower"].iloc[-1]),
                "bb_middle": float(bb["bb_middle"].iloc[-1]),
                "momentum": float(roc_3.iloc[-1]) if not roc_3.empty else 0.0,
            }
        except Exception:
            logger.exception("Fast indicator computation failed")
            return None

    # ── Sub-strategy signals ────────────────────────────────────────────

    @staticmethod
    def _rsi_signal(ind: dict) -> tuple[str | None, str]:
        rsi = ind.get("rsi")
        if rsi is None:
            return None, ""
        if rsi < 30:
            return "CALL", f"RSI oversold ({rsi:.1f})"
        if rsi > 70:
            return "PUT", f"RSI overbought ({rsi:.1f})"
        # Mid-range bias
        if rsi < 45:
            return "CALL", f"RSI low-range ({rsi:.1f})"
        if rsi > 55:
            return "PUT", f"RSI high-range ({rsi:.1f})"
        return None, ""

    @staticmethod
    def _ema_signal(ind: dict) -> tuple[str | None, str]:
        fast = ind.get("ema_fast", 0)
        medium = ind.get("ema_medium", 0)
        slow = ind.get("ema_slow", 0)
        if fast > medium > slow:
            return "CALL", "EMA bullish (5>10>20)"
        if fast < medium < slow:
            return "PUT", "EMA bearish (5<10<20)"
        return None, ""

    @staticmethod
    def _macd_signal(ind: dict) -> tuple[str | None, str]:
        line = ind.get("macd_line", 0)
        sig = ind.get("macd_signal", 0)
        hist = ind.get("macd_hist", 0)
        if line > sig and hist > 0:
            return "CALL", "MACD bullish"
        if line < sig and hist < 0:
            return "PUT", "MACD bearish"
        return None, ""

    @staticmethod
    def _bollinger_signal(ind: dict) -> tuple[str | None, str]:
        close = ind.get("close", 0)
        lower = ind.get("bb_lower", 0)
        upper = ind.get("bb_upper", 0)
        if close and lower and close <= lower:
            return "CALL", "Price at BB lower band"
        if close and upper and close >= upper:
            return "PUT", "Price at BB upper band"
        return None, ""

    @staticmethod
    def _momentum_signal(ind: dict) -> tuple[str | None, str]:
        mom = ind.get("momentum", 0)
        if mom > 0.005:
            return "CALL", f"Strong upward momentum ({mom:.3f})"
        if mom < -0.005:
            return "PUT", f"Strong downward momentum ({mom:.3f})"
        return None, ""

    # ── Consensus ───────────────────────────────────────────────────────

    @staticmethod
    def _consensus(votes: list[str]) -> str:
        """Determine CALL / PUT / NEUTRAL from collected votes."""
        if not votes:
            return "NEUTRAL"
        calls = sum(1 for v in votes if v == "CALL")
        puts = sum(1 for v in votes if v == "PUT")
        if calls >= 3:
            return "CALL"
        if puts >= 3:
            return "PUT"
        return "NEUTRAL"
