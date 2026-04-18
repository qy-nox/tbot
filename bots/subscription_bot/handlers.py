"""High-level subscription bot handlers."""

from __future__ import annotations

from bots.subscription_bot.messages import payment_prompt, status_message, welcome_message
from bots.subscription_bot.payment_handler import PaymentHandler, PaymentMethod, PaymentRequest

_payment = PaymentHandler()


def handle_start() -> str:
    return welcome_message()


def handle_payment(*, user_id: int, method: str, amount: float, transaction_id: str) -> str:
    request = PaymentRequest(
        user_id=user_id,
        method=PaymentMethod(method),
        amount=amount,
        transaction_id=transaction_id,
    )
    _payment.submit(request)
    return payment_prompt(method)


def handle_status(status: str) -> str:
    return status_message(status)
