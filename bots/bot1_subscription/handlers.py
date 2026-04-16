"""High-level subscription bot handlers."""

from bots.bot1_subscription.keyboard import plans_keyboard
from bots.bot1_subscription.payment_handler import create_pending_payment
from bots.bot1_subscription.utils import format_plan_catalog, format_welcome_message


def handle_start() -> str:
    return format_welcome_message()


def handle_plans() -> dict[str, object]:
    return {"text": format_plan_catalog(), "keyboard": plans_keyboard()}


def handle_subscribe(db, *, user_id: int, tier: str) -> str:
    payment = create_pending_payment(db, user_id=user_id, tier=tier)
    return f"Payment created (id={payment.id}, status={payment.status})"
