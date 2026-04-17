"""Simple storage helpers for subscription applications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from signal_platform.models import Payment, User, get_session


@dataclass
class SubscriptionApplication:
    username: str
    user_id: int
    telegram_id: str
    subscription_plan: str
    payment_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_id: str | None = None
    status: str = "pending_admin_approval"


_STORE: dict[int, SubscriptionApplication] = {}


def save_application(application: SubscriptionApplication) -> SubscriptionApplication:
    _STORE[application.user_id] = application
    return application


def _from_db(db: Session, user_id: int) -> Optional[SubscriptionApplication]:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return None
    payment = (
        db.query(Payment)
        .filter(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc())
        .first()
    )
    return SubscriptionApplication(
        username=user.username,
        user_id=user.id,
        telegram_id=user.telegram_chat_id or str(user.id),
        subscription_plan=user.subscription_tier.value,
        payment_date=(payment.created_at if payment and payment.created_at else datetime.now(timezone.utc)),
        transaction_id=(payment.provider_tx_id if payment else None),
        status=(payment.status if payment else "active"),
    )


def get_application(user_id: int) -> SubscriptionApplication | None:
    app = _STORE.get(user_id)
    if app is not None:
        return app
    db = get_session()
    try:
        return _from_db(db, user_id)
    finally:
        db.close()


def all_applications() -> list[SubscriptionApplication]:
    return list(_STORE.values())
