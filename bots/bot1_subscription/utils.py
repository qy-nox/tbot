"""Utility helpers for Bot 1 text formatting."""

from __future__ import annotations

from signal_platform.models import SubscriptionTier

PLAN_DESCRIPTIONS = {
    SubscriptionTier.FREE: "basic access",
    SubscriptionTier.PREMIUM: "full crypto + binary",
    SubscriptionTier.VIP: "all channels and priority support",
}


def format_welcome_message() -> str:
    """Return the Bot 1 welcome message."""
    return "Welcome! Use /plans to view subscription options."


def format_plan_catalog() -> str:
    """Return a human-readable summary of available plans."""
    return (
        f"- {SubscriptionTier.FREE.value}: {PLAN_DESCRIPTIONS[SubscriptionTier.FREE]}\n"
        f"- {SubscriptionTier.PREMIUM.value}: {PLAN_DESCRIPTIONS[SubscriptionTier.PREMIUM]}\n"
        f"- {SubscriptionTier.VIP.value}: {PLAN_DESCRIPTIONS[SubscriptionTier.VIP]}"
    )
