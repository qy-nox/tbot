"""Over-trading and revenge-trading prevention rules."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone


class TradeLimiter:
    def __init__(self, max_trades_per_day: int = 5, max_trades_per_pair_per_day: int = 2, min_minutes_between_signals: int = 30) -> None:
        self.max_trades_per_day = max_trades_per_day
        self.max_trades_per_pair_per_day = max_trades_per_pair_per_day
        self.min_minutes_between_signals = min_minutes_between_signals

        self.trades_by_day: defaultdict[str, int] = defaultdict(int)
        self.trades_by_pair_day: defaultdict[tuple[str, str], int] = defaultdict(int)
        self.last_trade_at: datetime | None = None
        self.loss_streak = 0

    def can_trade(self, *, pair: str, now: datetime) -> tuple[bool, str]:
        now_utc = now.astimezone(timezone.utc)
        day_key = now_utc.date().isoformat()
        pair_key = (pair, day_key)

        if self.trades_by_day[day_key] >= self.max_trades_per_day:
            return False, "daily trade limit reached"
        if self.trades_by_pair_day[pair_key] >= self.max_trades_per_pair_per_day:
            return False, "pair trade limit reached"

        if self.last_trade_at is not None:
            mins = (now_utc - self.last_trade_at).total_seconds() / 60
            if mins < self.min_minutes_between_signals:
                return False, "minimum spacing not met"

        if self.loss_streak >= 3:
            return False, "loss streak cool-down (until tomorrow)"
        if self.loss_streak == 2 and self.last_trade_at and now_utc < self.last_trade_at + timedelta(hours=2):
            return False, "2-loss cool-down"
        if self.loss_streak == 1 and self.last_trade_at and now_utc < self.last_trade_at + timedelta(hours=1):
            return False, "post-loss cool-down"

        return True, "ok"

    def register_trade(self, *, pair: str, now: datetime, won: bool) -> None:
        now_utc = now.astimezone(timezone.utc)
        day_key = now_utc.date().isoformat()
        self.trades_by_day[day_key] += 1
        self.trades_by_pair_day[(pair, day_key)] += 1
        self.last_trade_at = now_utc
        if won:
            self.loss_streak = 0
        else:
            self.loss_streak += 1
