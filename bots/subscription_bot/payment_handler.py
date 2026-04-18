"""Payment handling for Binance P2P, bKash and manual bank verification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PaymentMethod(str, Enum):
    BINANCE = "binance_p2p"
    BKASH = "bkash"
    BANK = "manual_bank"


@dataclass(frozen=True)
class PaymentRequest:
    user_id: int
    method: PaymentMethod
    amount: float
    transaction_id: str


class PaymentHandler:
    """In-memory compatibility payment processor."""

    def __init__(self) -> None:
        self._queue: dict[str, PaymentRequest] = {}

    def submit(self, request: PaymentRequest) -> str:
        self._queue[request.transaction_id] = request
        return "queued"

    def verify(self, transaction_id: str, approved: bool) -> str:
        if transaction_id not in self._queue:
            return "not_found"
        return "approved" if approved else "rejected"
