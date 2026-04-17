"""Payment flow implementation for subscription bot."""

from __future__ import annotations

from datetime import datetime, timezone

from bots.bot_subscription.storage import SubscriptionApplication, get_application, save_application
from signal_platform.models import Payment, SubscriptionTier, User, get_session, init_db
from signal_platform.services.subscription_service import SubscriptionService


def _safe_tier(plan: str) -> SubscriptionTier:
    return {
        "free": SubscriptionTier.FREE,
        "premium": SubscriptionTier.PREMIUM,
        "vip": SubscriptionTier.VIP,
    }.get(plan.lower(), SubscriptionTier.PREMIUM)


def _get_or_create_user(*, user_id: int, username: str, telegram_id: str) -> User:
    db = get_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            user = db.query(User).filter(User.telegram_chat_id == telegram_id).first()
        if user is None:
            user = User(
                id=user_id,
                username=(username or f"tg_{user_id}")[:50],
                email=f"tg_{user_id}@tbot.local",
                password_hash="telegram-user",
                telegram_chat_id=telegram_id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


def begin_subscription(*, username: str, user_id: int, telegram_id: str, plan: str) -> SubscriptionApplication:
    init_db()
    user = _get_or_create_user(user_id=user_id, username=username, telegram_id=telegram_id)
    db = get_session()
    try:
        SubscriptionService.seed_plans(db)
        tier = _safe_tier(plan)
        SubscriptionService.create_payment(db, user_id=user.id, tier=tier, provider="telegram", period="monthly")
        app = SubscriptionApplication(
            username=user.username,
            user_id=user.id,
            telegram_id=telegram_id,
            subscription_plan=tier.value,
            payment_date=datetime.now(timezone.utc),
            status="pending",
        )
        return save_application(app)
    finally:
        db.close()


def submit_transaction(user_id: int, tx_id: str) -> str:
    init_db()
    app = get_application(user_id)
    if app is None:
        return "No subscription found"
    app.transaction_id = tx_id
    save_application(app)

    db = get_session()
    try:
        payment = (
            db.query(Payment)
            .filter(Payment.user_id == user_id, Payment.status == "pending")
            .order_by(Payment.created_at.desc())
            .first()
        )
        if payment is not None:
            SubscriptionService.confirm_payment(db, payment.id, tx_id)
            app.status = "completed"
            save_application(app)
    finally:
        db.close()
    return "✅ Payment confirmed"


def approve_subscription(user_id: int) -> str:
    app = get_application(user_id)
    if app is None:
        return "No subscription found"
    app.status = "approved"
    save_application(app)
    return "Payment Approved! Congratulations!"
