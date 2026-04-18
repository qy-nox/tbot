"""Payment processing service for Binance, bKash, and manual bank."""

from __future__ import annotations

from database.models import Payment

ALLOWED_METHODS = {"binance_p2p", "bkash", "manual_bank"}


def submit_payment(db, *, user_id: int, amount: float, method: str, transaction_id: str) -> Payment:
    if method not in ALLOWED_METHODS:
        raise ValueError(f"Unsupported payment method: {method}")
    payment = Payment(user_id=user_id, amount=amount, method=method, transaction_id=transaction_id)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
