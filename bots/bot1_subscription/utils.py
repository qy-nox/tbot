"""Utility helpers for Bot 1 text formatting."""

from __future__ import annotations

from signal_platform.models import SubscriptionTier


def format_welcome_message() -> str:
    """Return the Bot 1 welcome message."""
    return "Welcome! Use /plans to view subscription options."


def format_plan_catalog() -> str:
    """Return a human-readable summary of available plans."""
    return (
        f"- {SubscriptionTier.FREE.value}: basic access\n"
        f"- {SubscriptionTier.PREMIUM.value}: full crypto + binary\n"
        f"- {SubscriptionTier.VIP.value}: all channels and priority support"
    )
