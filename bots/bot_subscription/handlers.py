"""Command handlers for the subscription bot."""

from __future__ import annotations

from bots.bot_subscription.keyboard import continue_keyboard, payment_options_keyboard, plans_keyboard
from bots.bot_subscription.payment_flow import begin_subscription, submit_transaction
from bots.bot_subscription.storage import get_application


def handle_start() -> dict[str, object]:
    return {
        "text": "Welcome! Start your subscription journey.",
        "keyboard": continue_keyboard(),
    }


def handle_plans() -> dict[str, object]:
    return {"text": "Choose your subscription plan", "keyboard": plans_keyboard()}


def handle_subscribe(*, username: str, user_id: int, telegram_id: str, plan: str) -> dict[str, object]:
    begin_subscription(username=username, user_id=user_id, telegram_id=telegram_id, plan=plan)
    return {"text": "Select payment option", "keyboard": payment_options_keyboard()}


def handle_transaction(*, user_id: int, transaction_id: str) -> str:
    return submit_transaction(user_id, transaction_id)


def handle_status(user_id: int) -> str:
    app = get_application(user_id)
    if app is None:
        return "No subscription found"
    return f"Plan: {app.subscription_plan} | Status: {app.status}"


def handle_billing(user_id: int) -> str:
    app = get_application(user_id)
    if app is None or app.transaction_id is None:
        return "No billing history"
    return f"Last payment tx: {app.transaction_id} on {app.payment_date:%Y-%m-%d}"
