"""Billing utilities."""

from __future__ import annotations


def create_invoice(user_id: int, amount: float, currency: str = "USD") -> dict:
    return {"user_id": user_id, "amount": amount, "currency": currency, "status": "created"}
