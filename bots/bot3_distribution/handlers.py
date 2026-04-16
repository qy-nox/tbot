"""High-level handlers for Bot 3 signal distribution flows."""

from __future__ import annotations

from bots.bot3_distribution.distributor import distribute_signal
from bots.bot3_distribution.signal_validator import is_valid_signal


def handle_distribute(db, signal) -> str:
    """Validate and distribute a signal, returning a user-friendly status."""
    if not is_valid_signal(signal):
        return "Invalid or missing signal"
    deliveries = distribute_signal(db, signal)
    return f"Delivered to {len(deliveries)} targets"

