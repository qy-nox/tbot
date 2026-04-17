"""Payment review helpers for admin bot."""

from __future__ import annotations

def pending_payments(db):
    return []


def approve_payment(db, payment_id, tx_id):
    return None


def reject_payment(db, payment_id):
    return "❌ Payment rejected"
