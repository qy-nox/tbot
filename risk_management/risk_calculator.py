"""Risk metric calculations."""

from __future__ import annotations

import math


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    if avg_loss <= 0:
        return 0.0
    b = avg_win / avg_loss
    return max(0.0, (win_rate * b - (1 - win_rate)) / b)


def sharpe_ratio(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    return 0.0 if std == 0 else mean / std
