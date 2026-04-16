"""Payment flow implementation for subscription bot."""

from __future__ import annotations

from bots.bot_subscription.storage import SubscriptionApplication, get_application, save_application


def begin_subscription(*, username: str, user_id: int, telegram_id: str, plan: str) -> SubscriptionApplication:
    application = SubscriptionApplication(
        username=username,
        user_id=user_id,
        telegram_id=telegram_id,
        subscription_plan=plan,
    )
    return save_application(application)


def submit_transaction(user_id: int, transaction_id: str) -> str:
    application = get_application(user_id)
    if application is None:
        return "No active subscription request found."
    application.transaction_id = transaction_id
    application.status = "waiting_admin_approval"
    return "Waiting for admin approval"


def approve_subscription(user_id: int) -> str:
    application = get_application(user_id)
    if application is None:
        return "Subscription request not found"
    application.status = "approved"
    return "Payment Approved! Congratulations!"
