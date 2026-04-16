"""Backtest report generation helpers."""

from __future__ import annotations


def generate_report(metrics: dict) -> str:
    return "\n".join([
        "Advanced Backtest Report",
        f"Trades: {metrics.get('total_trades', 0)}",
        f"Win Rate: {metrics.get('win_rate', 0):.2%}" if isinstance(metrics.get('win_rate', 0), float) else f"Win Rate: {metrics.get('win_rate', 0)}",
        f"Return: {metrics.get('total_return_pct', 0)}%",
    ])
