"""Inline keyboard helpers for Bot 1 subscription flows."""

from __future__ import annotations

from signal_platform.models import SubscriptionTier


def plans_keyboard() -> list[dict[str, str]]:
    """Return a simple plan selection keyboard model."""
    return [
        {"text": "Free", "callback_data": f"subscribe:{SubscriptionTier.FREE.value}"},
        {"text": "Premium", "callback_data": f"subscribe:{SubscriptionTier.PREMIUM.value}"},
        {"text": "VIP", "callback_data": f"subscribe:{SubscriptionTier.VIP.value}"},
    ]
