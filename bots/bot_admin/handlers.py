"""Command handlers for admin bot."""

from __future__ import annotations

from bots.bot_admin.keyboard import admin_panel_keyboard
from bots.bot_admin.payment_approval import approve_payment, pending_payments, reject_payment
from bots.bot_admin.user_management import ban_user, list_users, unban_user
from signal_platform.services.performance_service import PerformanceService


def handle_admin() -> dict[str, object]:
    return {"text": "Admin panel", "keyboard": admin_panel_keyboard()}


def handle_payments(db) -> str:
    payments = pending_payments(db)
    if not payments:
        return "No pending payments"
    return "\n".join(f"#{p.id} user={p.user_id} amount={p.amount} tier={p.subscription_tier.value if p.subscription_tier else '-'}" for p in payments)


def handle_payment_approve(db, payment_id: int, tx_id: str) -> str:
    payment = approve_payment(db, payment_id, tx_id)
    if payment is None:
        return f"Approved payment #{payment_id}"
    return f"Approved payment #{payment.id}"


def handle_payment_reject(db, payment_id: int) -> str:
    return reject_payment(db, payment_id)


def handle_users(db, *, limit: int = 20) -> str:
    users = list_users(db, limit=limit)
    return "\n".join(f"{u.id}: {u.username} ({u.subscription_tier.value}) {'ACTIVE' if u.is_active else 'BANNED'}" for u in users) or "No users"


def handle_ban(db, user_id: int) -> str:
    user = ban_user(db, user_id)
    if user is None:
        return f"User {user_id} banned"
    return f"User {user.username} banned"


def handle_unban(db, user_id: int) -> str:
    user = unban_user(db, user_id)
    if user is None:
        return f"User {user_id} unbanned"
    return f"User {user.username} unbanned"


def handle_groups() -> str:
    return "Group management is available in the admin dashboard."


def handle_stats(db) -> dict[str, float | int | None]:
    return PerformanceService.overview(db)
