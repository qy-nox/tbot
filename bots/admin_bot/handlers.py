"""Admin bot command handlers."""

from __future__ import annotations

from bots.admin_bot.analytics import dashboard_stats
from bots.admin_bot.management import list_signals, list_users


def handle_dashboard(db) -> dict[str, object]:
    return dashboard_stats(db)


def handle_users(db, limit: int = 20) -> str:
    users = list_users(db, limit=limit)
    return "\n".join(f"{u.id} | {u.username or 'N/A'}" for u in users) or "No users"


def handle_signals(db, limit: int = 20) -> str:
    signals = list_signals(db, limit=limit)
    return "\n".join(
        f"{s.id} | {s.pair or 'N/A'} | {s.direction or 'N/A'}" for s in signals
    ) or "No signals"
