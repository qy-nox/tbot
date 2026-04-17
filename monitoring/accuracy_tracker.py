"""Signal accuracy tracking across pairs, timeframe and strategy."""

from __future__ import annotations

from collections import defaultdict


class AccuracyTracker:
    def __init__(self) -> None:
        self.records: list[dict] = []
        self._stats = defaultdict(lambda: {"wins": 0, "losses": 0})

    def record(self, *, pair: str, timeframe: str, strategy: str, won: bool) -> None:
        row = {"pair": pair, "timeframe": timeframe, "strategy": strategy, "won": won}
        self.records.append(row)

        keys = [
            ("pair", pair),
            ("timeframe", timeframe),
            ("strategy", strategy),
        ]
        for key in keys:
            bucket = self._stats[key]
            if won:
                bucket["wins"] += 1
            else:
                bucket["losses"] += 1

    def win_rate(self, scope: str, value: str) -> float:
        bucket = self._stats[(scope, value)]
        total = bucket["wins"] + bucket["losses"]
        if total == 0:
            return 0.0
        return round((bucket["wins"] / total) * 100, 2)

    def overall_win_rate(self) -> float:
        wins = sum(1 for r in self.records if r["won"])
        total = len(self.records)
        if total == 0:
            return 0.0
        return round((wins / total) * 100, 2)
