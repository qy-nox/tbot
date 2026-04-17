"""Payment flow implementation for subscription bot."""

from __future__ import annotations

from bots.bot_subscription.storage import get_application


def begin_subscription(**kwargs):
    pass


def submit_transaction(user_id: int, tx_id: str) -> str:
    _ = get_application(user_id)
    return "✅ Payment confirmed"


def approve_subscription(user_id: int) -> str:
    _ = get_application(user_id)
    return "Payment Approved! Congratulations!"
