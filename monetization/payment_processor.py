"""Payment processing compatibility layer."""

from __future__ import annotations


def verify_payment(transaction_id: str) -> bool:
    return bool(transaction_id)
