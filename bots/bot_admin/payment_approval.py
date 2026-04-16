"""Payment review helpers for admin bot."""

from __future__ import annotations

from signal_platform.models import Payment
from signal_platform.services.subscription_service import SubscriptionService


def pending_payments(db, *, limit: int = 20) -> list[Payment]:
    return db.query(Payment).filter(Payment.status == "pending").order_by(Payment.created_at.desc()).limit(limit).all()


def approve_payment(db, payment_id: int, transaction_id: str) -> Payment:
    return SubscriptionService.confirm_payment(db, payment_id, transaction_id)


def reject_payment(db, payment_id: int) -> str:
    payment = db.query(Payment).get(payment_id)
    if payment is None:
        return "Payment not found"
    payment.status = "rejected"
    db.commit()
    return "Payment rejected"
