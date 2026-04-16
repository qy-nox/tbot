"""High-level handlers for Bot 3 signal distribution flows."""

from __future__ import annotations

from sqlalchemy.orm import Session

from bots.bot3_distribution.distributor import distribute_signal
from bots.bot3_distribution.signal_validator import is_valid_signal
from signal_platform.models import SignalRecord


def handle_distribute(db: Session, signal: SignalRecord | None) -> tuple[bool, str]:
    """Validate and distribute a signal, returning status and user-friendly text."""
    if not is_valid_signal(signal):
        return False, "Invalid or missing signal"
    deliveries = distribute_signal(db, signal)
    return True, f"Delivered to {len(deliveries)} targets"
