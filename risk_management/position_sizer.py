"""
Position sizing and risk management module.
Auto position sizing, volatility-based stop losses, Kelly Criterion,
drawdown protection, and anti-overtrading logic.
"""

import logging
import math
from dataclasses import dataclass

from config.settings import Settings

logger = logging.getLogger("trading_bot.position_sizer")


@dataclass
class PositionPlan:
    """Computed position sizing and risk levels."""

    pair: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    position_size: float  # in base currency units
    position_value: float  # in quote currency
    risk_amount: float
    risk_reward_ratio: float
    confidence: float


class PositionSizer:
    """Calculate position sizes and stop/take-profit levels."""

    def __init__(
        self,
        capital: float | None = None,
        risk_per_trade: float | None = None,
    ) -> None:
        self.capital = capital or Settings.INITIAL_CAPITAL
        self.risk_per_trade = risk_per_trade or Settings.RISK_PER_TRADE
        self.max_drawdown = Settings.MAX_DRAWDOWN
        self.max_open_trades = Settings.MAX_OPEN_TRADES
        self.sl_atr_mult = Settings.STOP_LOSS_ATR_MULTIPLIER
        self.tp_levels = Settings.TAKE_PROFIT_LEVELS
        self.open_trades: int = 0
        self.peak_capital: float = self.capital
        logger.info(
            "PositionSizer: capital=%.2f, risk_per_trade=%.1f%%",
            self.capital,
            self.risk_per_trade * 100,
        )

    # ── Core sizing ─────────────────────────────────────────────────────

    def compute(
        self,
        pair: str,
        direction: str,
        entry_price: float,
        atr: float,
        confidence: float = 1.0,
    ) -> PositionPlan | None:
        """Compute a full position plan or return None if blocked."""
        # Pre-flight checks
        if not self._passes_checks():
            return None

        # Stop loss
        sl_distance = atr * self.sl_atr_mult
        if direction == "BUY":
            stop_loss = entry_price - sl_distance
            tp1 = entry_price + sl_distance * self.tp_levels[0]
            tp2 = entry_price + sl_distance * self.tp_levels[1]
            tp3 = entry_price + sl_distance * self.tp_levels[2]
        else:
            stop_loss = entry_price + sl_distance
            tp1 = entry_price - sl_distance * self.tp_levels[0]
            tp2 = entry_price - sl_distance * self.tp_levels[1]
            tp3 = entry_price - sl_distance * self.tp_levels[2]

        risk_amount = self.capital * self.risk_per_trade * confidence
        position_size = risk_amount / sl_distance if sl_distance > 0 else 0
        position_value = position_size * entry_price

        rr = (abs(tp2 - entry_price) / sl_distance) if sl_distance > 0 else 0

        plan = PositionPlan(
            pair=pair,
            direction=direction,
            entry_price=entry_price,
            stop_loss=round(stop_loss, 8),
            take_profit_1=round(tp1, 8),
            take_profit_2=round(tp2, 8),
            take_profit_3=round(tp3, 8),
            position_size=round(position_size, 8),
            position_value=round(position_value, 2),
            risk_amount=round(risk_amount, 2),
            risk_reward_ratio=round(rr, 2),
            confidence=confidence,
        )
        logger.info(
            "Position plan: %s %s @ %.2f | SL=%.2f | TP2=%.2f | size=%.6f | R:R=1:%.1f",
            direction,
            pair,
            entry_price,
            stop_loss,
            tp2,
            position_size,
            rr,
        )
        return plan

    # ── Kelly Criterion ─────────────────────────────────────────────────

    def kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Return the Kelly Criterion fraction (capped at risk_per_trade)."""
        if avg_loss == 0:
            return self.risk_per_trade
        b = avg_win / avg_loss
        f = (win_rate * b - (1 - win_rate)) / b
        f = max(0.0, min(f, self.risk_per_trade * 2))  # cap at 2× base risk
        logger.debug("Kelly fraction: %.4f (WR=%.2f, b=%.2f)", f, win_rate, b)
        return f

    # ── Drawdown protection ─────────────────────────────────────────────

    def update_capital(self, new_capital: float) -> None:
        """Update capital and track peak for drawdown monitoring."""
        self.capital = new_capital
        self.peak_capital = max(self.peak_capital, new_capital)

    @property
    def current_drawdown(self) -> float:
        """Current drawdown as a positive fraction (0 = no drawdown)."""
        if self.peak_capital == 0:
            return 0.0
        return (self.peak_capital - self.capital) / self.peak_capital

    # ── Pre-flight checks ───────────────────────────────────────────────

    def _passes_checks(self) -> bool:
        """Return True if a new trade is allowed."""
        if self.open_trades >= self.max_open_trades:
            logger.warning(
                "Max open trades reached (%d/%d)",
                self.open_trades,
                self.max_open_trades,
            )
            return False

        dd = self.current_drawdown
        if dd >= self.max_drawdown:
            logger.warning(
                "Max drawdown breached (%.1f%% >= %.1f%%)",
                dd * 100,
                self.max_drawdown * 100,
            )
            return False

        return True

    # ── Trade lifecycle helpers ─────────────────────────────────────────

    def register_open(self) -> None:
        """Call when a trade is opened."""
        self.open_trades += 1

    def register_close(self, pnl: float) -> None:
        """Call when a trade is closed; updates capital."""
        self.open_trades = max(0, self.open_trades - 1)
        self.update_capital(self.capital + pnl)
        logger.info(
            "Trade closed PnL=%.2f | capital=%.2f | drawdown=%.1f%%",
            pnl,
            self.capital,
            self.current_drawdown * 100,
        )
