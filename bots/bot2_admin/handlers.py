"""Admin handler wrappers."""

from bots.bot2_admin.admin_commands import list_users


def handle_list_users(db, *, limit: int = 20) -> str:
    users = list_users(db, limit=limit)
    return "\n".join(f"{u.id}: {u.username} ({u.subscription_tier.value})" for u in users) or "No users"
