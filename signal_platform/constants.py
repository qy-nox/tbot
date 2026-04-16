"""Shared constants and compatibility enums for the signal platform."""

from __future__ import annotations

from signal_platform.models import (
    DeliveryChannel,
    DeliveryStatus,
    SignalDirection,
    SignalGrade,
    SignalOutcome,
    SignalType,
    SubscriptionTier,
)

DEFAULT_TIMEZONE = "UTC"
DEFAULT_CURRENCY = "USD"
ACCESS_TOKEN_TYPE = "bearer"

__all__ = [
    "DeliveryChannel",
    "DeliveryStatus",
    "SignalDirection",
    "SignalGrade",
    "SignalOutcome",
    "SignalType",
    "SubscriptionTier",
    "DEFAULT_TIMEZONE",
    "DEFAULT_CURRENCY",
    "ACCESS_TOKEN_TYPE",
]
