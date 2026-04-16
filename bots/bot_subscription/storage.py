"""Simple storage helpers for subscription applications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


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


def get_application(user_id: int) -> SubscriptionApplication | None:
    return _STORE.get(user_id)


def all_applications() -> list[SubscriptionApplication]:
    return list(_STORE.values())
