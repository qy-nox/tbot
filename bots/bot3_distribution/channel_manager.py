"""Channel and subscriber target helpers for Bot 3 distribution."""

from __future__ import annotations

import os
from typing import Iterable

from signal_platform.models import SignalRecord, User
from signal_platform.services.distribution_service import _can_receive


def broadcast_channels_from_env() -> list[str]:
    """Return configured broadcast channel IDs from environment."""
    raw = os.getenv("BROADCAST_TELEGRAM_CHANNELS", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def subscriber_chat_targets(signal: SignalRecord, users: Iterable[User]) -> list[str]:
    """Return telegram chat ids for users eligible for the given signal."""
    targets: list[str] = []
    for user in users:
        if user.telegram_chat_id and _can_receive(user, signal):
            targets.append(user.telegram_chat_id)
    return targets
