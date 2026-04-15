"""
Vectorized backtesting engine.
Computes Sharpe ratio, Sortino ratio, max drawdown, profit factor,
win rate, and per-trade logs.
"""

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config.settings import Settings
from core.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger("trading_bot.backtest_engine")


@dataclass
class BacktestResult:
    """Container for backtesting metrics."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    recovery_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    trade_log: list[dict] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


class BacktestEngine:
    """Run vectorized backtests on OHLCV data."""

    def __init__(
        self,
        initial_capital: float | None = None,
        commission: float | None = None,
        risk_per_trade: float | None = None,
        sl_atr_mult: float | None = None,
        tp_atr_mult: float = 2.0,
    ) -> None:
        self.initial_capital = initial_capital or Settings.BACKTEST_INITIAL_CAPITAL
        self.commission = commission or Settings.BACKTEST_COMMISSION
        self.risk_per_trade = risk_per_trade or Settings.RISK_PER_TRADE
        self.sl_atr_mult = sl_atr_mult or Settings.STOP_LOSS_ATR_MULTIPLIER
        self.tp_atr_mult = tp_atr_mult
        self.analyzer = TechnicalAnalyzer()

    # ── Main entry point ────────────────────────────────────────────────

    def run(self, df: pd.DataFrame, strategy_fn=None) -> BacktestResult:
        """Execute the backtest over *df* using *strategy_fn* for signals.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame indexed by datetime.
        strategy_fn : callable, optional
            ``strategy_fn(row_dict) -> 'BUY' | 'SELL' | None``.
            If None a simple RSI mean-reversion strategy is used.
        """
        if df.empty or len(df) < 50:
            logger.warning("Not enough data for backtesting (%d rows)", len(df))
            return BacktestResult()

        df = self._add_indicators(df)

        if strategy_fn is None:
            strategy_fn = self._default_strategy

        return self._simulate(df, strategy_fn)

    # ── Indicator pre-computation ───────────────────────────────────────

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["rsi"] = self.analyzer.compute_rsi(df)
        emas = self.analyzer.compute_ema_set(df)
        df["ema_fast"] = emas["ema_fast"]
        df["ema_medium"] = emas["ema_medium"]
        df["ema_slow"] = emas["ema_slow"]
        macd = self.analyzer.compute_macd(df)
        df["macd_line"] = macd["macd_line"]
        df["macd_signal"] = macd["signal_line"]
        df["atr"] = self.analyzer.compute_atr(df)
        df.dropna(inplace=True)
        return df

    # ── Default RSI strategy ────────────────────────────────────────────

    @staticmethod
    def _default_strategy(row: dict) -> str | None:
        """Simple RSI + EMA crossover strategy."""
        if row.get("rsi", 50) < 30 and row.get("ema_fast", 0) > row.get("ema_medium", 0):
            return "BUY"
        if row.get("rsi", 50) > 70 and row.get("ema_fast", 0) < row.get("ema_medium", 0):
            return "SELL"
        return None

    # ── Simulation loop ─────────────────────────────────────────────────

    def _simulate(self, df: pd.DataFrame, strategy_fn) -> BacktestResult:
        capital = self.initial_capital
        equity_curve: list[float] = [capital]
        trade_log: list[dict] = []
        position = None  # dict or None

        for i in range(len(df)):
            row = df.iloc[i].to_dict()
            row["_index"] = df.index[i]
            price = row["close"]
            atr = row.get("atr", 0)

            # Check exit conditions if in a position
            if position is not None:
                exit_price = self._check_exit(position, row)
                if exit_price is not None:
                    pnl = self._close_trade(position, exit_price)
                    capital += pnl - self.commission * abs(pnl)
                    equity_curve.append(capital)
                    trade_log.append(
                        {
                            "entry_time": position["entry_time"],
                            "exit_time": row["_index"],
                            "direction": position["direction"],
                            "entry": position["entry"],
                            "exit": exit_price,
                            "pnl": round(pnl, 4),
                        }
                    )
                    position = None
                    continue

            # Generate signal
            if position is None:
                signal = strategy_fn(row)
                if signal in ("BUY", "SELL") and atr > 0:
                    sl_dist = atr * self.sl_atr_mult
                    risk_amount = capital * self.risk_per_trade
                    size = risk_amount / sl_dist

                    if signal == "BUY":
                        sl = price - sl_dist
                        tp = price + sl_dist * self.tp_atr_mult
                    else:
                        sl = price + sl_dist
                        tp = price - sl_dist * self.tp_atr_mult

                    position = {
                        "direction": signal,
                        "entry": price,
                        "sl": sl,
                        "tp": tp,
                        "size": size,
                        "entry_time": row["_index"],
                    }

            equity_curve.append(capital)

        # Force-close open position at end
        if position is not None:
            exit_price = df["close"].iloc[-1]
            pnl = self._close_trade(position, exit_price)
            capital += pnl - self.commission * abs(pnl)
            equity_curve.append(capital)
            trade_log.append(
                {
                    "entry_time": position["entry_time"],
                    "exit_time": df.index[-1],
                    "direction": position["direction"],
                    "entry": position["entry"],
                    "exit": exit_price,
                    "pnl": round(pnl, 4),
                }
            )

        return self._compile_metrics(trade_log, equity_curve)

    # ── Exit check ──────────────────────────────────────────────────────

    @staticmethod
    def _check_exit(position: dict, row: dict) -> float | None:
        high, low = row["high"], row["low"]
        if position["direction"] == "BUY":
            if low <= position["sl"]:
                return position["sl"]
            if high >= position["tp"]:
                return position["tp"]
        else:
            if high >= position["sl"]:
                return position["sl"]
            if low <= position["tp"]:
                return position["tp"]
        return None

    @staticmethod
    def _close_trade(position: dict, exit_price: float) -> float:
        size = position["size"]
        if position["direction"] == "BUY":
            return (exit_price - position["entry"]) * size
        return (position["entry"] - exit_price) * size

    # ── Metrics ─────────────────────────────────────────────────────────

    def _compile_metrics(
        self, trade_log: list[dict], equity_curve: list[float]
    ) -> BacktestResult:
        result = BacktestResult(trade_log=trade_log, equity_curve=equity_curve)
        if not trade_log:
            return result

        pnls = [t["pnl"] for t in trade_log]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        result.total_trades = len(pnls)
        result.winning_trades = len(wins)
        result.losing_trades = len(losses)
        result.win_rate = len(wins) / len(pnls) if pnls else 0
        result.total_return = sum(pnls)
        result.total_return_pct = result.total_return / self.initial_capital * 100
        result.avg_win = np.mean(wins) if wins else 0.0
        result.avg_loss = np.mean(losses) if losses else 0.0

        # Sharpe / Sortino (annualised, assuming ~365 trades/year as proxy)
        arr = np.array(pnls, dtype=float)
        if arr.std() > 0:
            result.sharpe_ratio = float(np.mean(arr) / np.std(arr) * np.sqrt(365))
        downside = arr[arr < 0]
        if len(downside) > 0 and downside.std() > 0:
            result.sortino_ratio = float(np.mean(arr) / downside.std() * np.sqrt(365))

        # Max drawdown from equity curve
        eq = np.array(equity_curve, dtype=float)
        peak = np.maximum.accumulate(eq)
        dd = (peak - eq) / np.where(peak > 0, peak, 1)
        result.max_drawdown = float(dd.max())

        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Recovery factor
        if result.max_drawdown > 0:
            result.recovery_factor = result.total_return / (
                result.max_drawdown * self.initial_capital
            )

        logger.info(
            "Backtest: trades=%d WR=%.1f%% return=%.2f%% sharpe=%.2f dd=%.1f%%",
            result.total_trades,
            result.win_rate * 100,
            result.total_return_pct,
            result.sharpe_ratio,
            result.max_drawdown * 100,
        )
        return result
