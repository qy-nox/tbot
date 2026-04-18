"""Subscription tier service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database.models import Subscription


def create_subscription(db, *, user_id: int, tier: str, signal_type: str, amount: float, payment_method: str, transaction_id: str) -> Subscription:
    row = Subscription(
        user_id=user_id,
        tier=tier,
        signal_type=signal_type,
        amount=amount,
        payment_method=payment_method,
        transaction_id=transaction_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
