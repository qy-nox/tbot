"""Real-time drawdown monitor."""

from __future__ import annotations


class DrawdownMonitor:
    def __init__(self) -> None:
        self.peak = 0.0

    def update(self, equity: float) -> float:
        self.peak = max(self.peak, equity)
        if self.peak <= 0:
            return 0.0
        return (self.peak - equity) / self.peak
