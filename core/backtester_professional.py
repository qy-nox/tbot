"""Professional-grade backtesting helpers and summary metrics."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class BacktestMetrics:
    total_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    net_profit: float


class ProfessionalBacktester:
    def summarize(self, trade_pnls: list[float]) -> BacktestMetrics:
        if not trade_pnls:
            return BacktestMetrics(0, 0.0, 0.0, 0.0, 0.0, 0.0)

        wins = [p for p in trade_pnls if p > 0]
        losses = [p for p in trade_pnls if p < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss else float("inf")

        mean = sum(trade_pnls) / len(trade_pnls)
        variance = sum((x - mean) ** 2 for x in trade_pnls) / max(len(trade_pnls) - 1, 1)
        sharpe = 0.0 if variance == 0 else mean / (variance ** 0.5)

        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for pnl in trade_pnls:
            equity += pnl
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)

        return BacktestMetrics(
            total_trades=len(trade_pnls),
            win_rate=round((len(wins) / len(trade_pnls)) * 100, 2),
            profit_factor=round(profit_factor, 4) if profit_factor != float("inf") else float("inf"),
            sharpe_ratio=round(sharpe, 4),
            max_drawdown=round(max_dd, 4),
            net_profit=round(sum(trade_pnls), 4),
        )

    def monte_carlo(self, trade_pnls: list[float], iterations: int = 10_000) -> dict[str, float]:
        if not trade_pnls:
            return {"worst_drawdown": 0.0, "median_drawdown": 0.0}

        drawdowns: list[float] = []
        for _ in range(max(iterations, 1)):
            shuffled = trade_pnls[:]
            random.shuffle(shuffled)
            summary = self.summarize(shuffled)
            drawdowns.append(summary.max_drawdown)

        drawdowns.sort()
        return {
            "worst_drawdown": drawdowns[-1],
            "median_drawdown": drawdowns[len(drawdowns) // 2],
            "iterations": float(iterations),
        }
