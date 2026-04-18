"""Admin bot command handlers."""

from __future__ import annotations

from bots.admin_bot.analytics import dashboard_stats
from bots.admin_bot.management import (
    add_group,
    list_groups,
    list_signals,
    list_users,
    remove_group,
    setup_groups,
    test_group_access,
)


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


def handle_setup_groups(db) -> str:
    groups = setup_groups(db)
    return f"Configured {len(groups)} group(s) from SIGNAL_GROUP_*_ID"


def handle_add_group(db, *, name: str, group_id: str, group_type: str = "HV", category: str = "crypto") -> str:
    row = add_group(db, name=name, group_id=group_id, group_type=group_type, category=category)
    return f"Added group: {row.name} ({row.group_id})"


def handle_list_groups(db) -> str:
    groups = list_groups(db)
    return "\n".join(f"{g.id} | {g.name} | {g.group_id}" for g in groups) or "No groups"


def handle_test_group(*, token: str, group_id: str) -> str:
    ok, detail = test_group_access(token=token, group_id=group_id)
    return f"{'OK' if ok else 'FAILED'}: {detail}"


def handle_remove_group(db, *, group_id: str) -> str:
    removed = remove_group(db, group_id=group_id)
    return "Removed" if removed else "Group not found"
