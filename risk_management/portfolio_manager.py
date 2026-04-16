"""Portfolio-level exposure controls."""

from __future__ import annotations


class PortfolioManager:
    def __init__(self, max_positions: int = 5) -> None:
        self.max_positions = max_positions
        self.positions: dict[str, dict] = {}

    def can_open(self, pair: str) -> bool:
        return pair in self.positions or len(self.positions) < self.max_positions

    def open_position(self, pair: str, payload: dict) -> bool:
        if not self.can_open(pair):
            return False
        self.positions[pair] = payload
        return True

    def close_position(self, pair: str) -> None:
        self.positions.pop(pair, None)
