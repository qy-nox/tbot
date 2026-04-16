"""Monte Carlo simulation for strategy returns."""

from __future__ import annotations

import random


def simulate(returns: list[float], iterations: int = 1000, horizon: int = 100) -> list[float]:
    if not returns:
        return [0.0] * iterations
    outcomes: list[float] = []
    for _ in range(iterations):
        total = 0.0
        for _ in range(horizon):
            total += random.choice(returns)
        outcomes.append(total)
    return outcomes
