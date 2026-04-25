"""
Strategy engine – orchestrates multi-indicator consensus signals.
Applies filters (trend, momentum, volatility, ADX, news) before
emitting a final BUY / SELL / HOLD recommendation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from config.settings import Settings
from core.technical_analyzer import TechnicalAnalyzer
from core.sentiment_analyzer import SentimentAnalyzer, SentimentResult
from core.economic_calendar import EconomicCalendar

logger = logging.getLogger("trading_bot.strategy_engine")


@dataclass
class Signal:
    """Represents a trading signal."""

    timestamp: datetime
    pair: str
    direction: str  # BUY / SELL / HOLD
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    confidence: float
    trend: str
    reasons: list[str]
    strategy_name: str


class StrategyEngine:
    """Multi-indicator consensus + filter system."""

    def __init__(self) -> None:
        self.analyzer = TechnicalAnalyzer()
        self.sentiment = SentimentAnalyzer()
        self.cfg = Settings.INDICATORS
        self.filters = Settings.FILTERS
        self.calendar = EconomicCalendar(
            finnhub_key=Settings.FINNHUB_API_KEY,
            skip_minutes=Settings.HIGH_IMPACT_SKIP_MINUTES,
        )

    # ── Main evaluate ───────────────────────────────────────────────────

    def evaluate(
        self,
        pair: str,
        analysis: dict,
        sentiment: SentimentResult | None = None,
        atr: float | None = None,
    ) -> Signal | None:
        """Return a Signal if consensus is reached, otherwise None."""
        if not analysis:
            return None

        # Collect sub-strategy votes
        votes: list[str] = []
        reasons: list[str] = []

        rsi_vote, rsi_reason = self._rsi_strategy(analysis)
        if rsi_vote:
            votes.append(rsi_vote)
            reasons.append(rsi_reason)

        macd_vote, macd_reason = self._macd_strategy(analysis)
        if macd_vote:
            votes.append(macd_vote)
            reasons.append(macd_reason)

        ema_vote, ema_reason = self._ema_strategy(analysis)
        if ema_vote:
            votes.append(ema_vote)
            reasons.append(ema_reason)

        bb_vote, bb_reason = self._bollinger_strategy(analysis)
        if bb_vote:
            votes.append(bb_vote)
            reasons.append(bb_reason)

        # Consensus
        direction = self._consensus(votes)
        if direction == "HOLD":
            logger.debug("%s: no consensus (%s)", pair, votes)
            return None

        # Confidence = proportion of agreeing indicators
        total = max(len(votes), 1)
        agree = sum(1 for v in votes if v == direction)
        confidence = agree / total

        if confidence < Settings.MIN_SIGNAL_CONFIDENCE:
            logger.debug(
                "%s: confidence %.0f%% below threshold", pair, confidence * 100
            )
            return None

        # Apply filters
        if not self._apply_filters(analysis, sentiment):
            logger.debug("%s: filtered out", pair)
            return None

        # Build signal levels
        entry = analysis["close"]
        effective_atr = atr if atr else (analysis.get("atr") or 0)
        sl_dist = effective_atr * Settings.STOP_LOSS_ATR_MULTIPLIER

        if direction == "BUY":
            sl = entry - sl_dist
            tp1 = entry + sl_dist * Settings.TAKE_PROFIT_LEVELS[0]
            tp2 = entry + sl_dist * Settings.TAKE_PROFIT_LEVELS[1]
            tp3 = entry + sl_dist * Settings.TAKE_PROFIT_LEVELS[2]
        else:
            sl = entry + sl_dist
            tp1 = entry - sl_dist * Settings.TAKE_PROFIT_LEVELS[0]
            tp2 = entry - sl_dist * Settings.TAKE_PROFIT_LEVELS[1]
            tp3 = entry - sl_dist * Settings.TAKE_PROFIT_LEVELS[2]

        signal = Signal(
            timestamp=datetime.now(timezone.utc),
            pair=pair,
            direction=direction,
            entry_price=entry,
            stop_loss=round(sl, 8),
            take_profit_1=round(tp1, 8),
            take_profit_2=round(tp2, 8),
            take_profit_3=round(tp3, 8),
            confidence=round(confidence, 2),
            trend=analysis.get("trend", "UNKNOWN"),
            reasons=reasons,
            strategy_name="multi_indicator_consensus",
        )
        logger.info(
            "SIGNAL %s %s @ %.4f | conf=%.0f%% | reasons=%s",
            direction,
            pair,
            entry,
            confidence * 100,
            "; ".join(reasons),
        )
        return signal

    # ── Sub-strategies ──────────────────────────────────────────────────

    def _rsi_strategy(self, a: dict) -> tuple[str | None, str]:
        rsi = a.get("rsi")
        if rsi is None:
            return None, ""
        cfg = self.cfg["rsi"]
        if rsi < cfg["oversold"]:
            return "BUY", f"RSI oversold ({rsi:.1f})"
        if rsi > cfg["overbought"]:
            return "SELL", f"RSI overbought ({rsi:.1f})"
        return None, ""

    def _macd_strategy(self, a: dict) -> tuple[str | None, str]:
        line = a.get("macd_line")
        sig = a.get("macd_signal")
        if line is None or sig is None:
            return None, ""
        if line > sig:
            return "BUY", "MACD bullish crossover"
        if line < sig:
            return "SELL", "MACD bearish crossover"
        return None, ""

    def _ema_strategy(self, a: dict) -> tuple[str | None, str]:
        fast = a.get("ema_fast")
        medium = a.get("ema_medium")
        slow = a.get("ema_slow")
        if None in (fast, medium, slow):
            return None, ""
        if fast > medium > slow:
            return "BUY", "EMA bullish alignment (20>50>200)"
        if fast < medium < slow:
            return "SELL", "EMA bearish alignment (20<50<200)"
        return None, ""

    def _bollinger_strategy(self, a: dict) -> tuple[str | None, str]:
        close = a.get("close")
        lower = a.get("bb_lower")
        upper = a.get("bb_upper")
        if None in (close, lower, upper):
            return None, ""
        if close <= lower:
            return "BUY", "Price at BB lower band"
        if close >= upper:
            return "SELL", "Price at BB upper band"
        return None, ""

    # ── Consensus ───────────────────────────────────────────────────────

    @staticmethod
    def _consensus(votes: list[str]) -> str:
        if not votes:
            return "HOLD"
        buy = sum(1 for v in votes if v == "BUY")
        sell = sum(1 for v in votes if v == "SELL")
        min_agree = Settings.MIN_INDICATORS_AGREE
        if buy >= min_agree:
            return "BUY"
        if sell >= min_agree:
            return "SELL"
        return "HOLD"

    # ── Filters ─────────────────────────────────────────────────────────

    def _apply_filters(
        self, analysis: dict, sentiment: SentimentResult | None
    ) -> bool:
        f = self.filters

        # RHIC: High-Impact Calendar blackout
        if Settings.CALENDAR_ENABLED:
            try:
                if self.calendar.is_high_impact_window():
                    logger.info(
                        "RHIC blackout active – skipping signal during high-impact news window"
                    )
                    return False
            except Exception:
                logger.warning("RHIC calendar check failed (non-fatal)", exc_info=True)

        # Trend filter
        if f.get("trend_filter"):
            trend = analysis.get("trend", "SIDEWAYS")
            if trend == "SIDEWAYS":
                logger.debug("Trend filter: sideways market")
                return False

        # ADX filter
        if f.get("adx_filter"):
            adx = analysis.get("adx")
            if adx is not None and adx < f.get("min_adx", 20):
                logger.debug("ADX filter: ADX=%.1f < %d", adx, f["min_adx"])
                return False

        # News / sentiment filter
        if f.get("news_filter") and sentiment is not None:
            if sentiment.impact == "HIGH" and sentiment.label == "BEARISH":
                logger.debug("News filter: high-impact bearish news")
                return False

        return True
