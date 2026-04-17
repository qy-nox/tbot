"""Weekly performance aggregation utilities."""

from __future__ import annotations


class WeeklyPerformanceTracker:
    def summarize(self, trades: list[dict]) -> dict:
        if not trades:
            return {
                "total_signals": 0,
                "win_rate": 0.0,
                "profitable_trades": 0,
                "losing_trades": 0,
                "total_profit_loss": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "average_risk_reward": 0.0,
            }

        pnls = [float(t.get("pnl", 0.0)) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        rr_values = [float(t.get("risk_reward", 0.0)) for t in trades if t.get("risk_reward") is not None]

        return {
            "total_signals": len(trades),
            "win_rate": round((len(wins) / len(trades)) * 100, 2),
            "profitable_trades": len(wins),
            "losing_trades": len(losses),
            "total_profit_loss": round(sum(pnls), 4),
            "best_trade": round(max(pnls), 4),
            "worst_trade": round(min(pnls), 4),
            "average_risk_reward": round(sum(rr_values) / len(rr_values), 4) if rr_values else 0.0,
        }
