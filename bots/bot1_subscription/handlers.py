"""High-level subscription bot handlers."""

from bots.bot1_subscription.payment_handler import create_pending_payment


def handle_subscribe(db, *, user_id: int, tier: str) -> str:
    payment = create_pending_payment(db, user_id=user_id, tier=tier)
    return f"Payment created (id={payment.id}, status={payment.status})"
