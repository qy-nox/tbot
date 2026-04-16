"""Backtest report generation helpers."""

from __future__ import annotations


def generate_report(metrics: dict) -> str:
    win_rate = metrics.get("win_rate", 0)
    win_rate_text = (
        f"Win Rate: {win_rate:.2%}"
        if isinstance(win_rate, float)
        else f"Win Rate: {win_rate}"
    )
    return "\n".join([
        "Advanced Backtest Report",
        f"Trades: {metrics.get('total_trades', 0)}",
        win_rate_text,
        f"Return: {metrics.get('total_return_pct', 0)}%",
    ])
