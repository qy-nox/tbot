"""Command handlers for the subscription bot."""

from __future__ import annotations

from bots.bot_subscription.keyboard import continue_keyboard, payment_options_keyboard, plans_keyboard
from bots.bot_subscription.payment_flow import begin_subscription, submit_transaction
from bots.bot_subscription.storage import get_application
from signal_platform.models import get_session
from signal_platform.services.subscription_service import SubscriptionService


def _mask_tx(transaction_id: str) -> str:
    if len(transaction_id) <= 4:
        return "***"
    return f"***{transaction_id[-4:]}"


def handle_start() -> dict[str, object]:
    return {
        "text": "Welcome! Start your subscription journey.",
        "keyboard": continue_keyboard(),
    }


def handle_plans() -> dict[str, object]:
    db = get_session()
    try:
        SubscriptionService.seed_plans(db)
        plans = SubscriptionService.list_plans(db)
        lines = ["Choose your subscription plan:"]
        for plan in plans:
            lines.append(f"• {plan.name}: ${plan.price_monthly:.2f}/mo (${plan.price_yearly:.2f}/yr)")
        text = "\n".join(lines)
    finally:
        db.close()
    return {"text": text, "keyboard": plans_keyboard()}


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
    db = get_session()
    try:
        history = SubscriptionService.billing_history(db, user_id, limit=3)
    finally:
        db.close()
    if not history:
        return "No billing history"
    payment = history[0]
    tx = _mask_tx(payment.provider_tx_id or "----")
    payment_date = payment.created_at.strftime("%Y-%m-%d") if payment.created_at is not None else "unknown date"
    return f"Last payment tx: {tx} on {payment_date} ({payment.status})"
