"""Keyboard helpers for Bot 2 admin controls."""

from __future__ import annotations


def admin_keyboard() -> list[dict[str, str]]:
    """Return an admin action keyboard model."""
    return [
        {"text": "Stats", "callback_data": "admin:stats"},
        {"text": "Users", "callback_data": "admin:users"},
        {"text": "Revenue", "callback_data": "admin:revenue"},
        {"text": "Approve", "callback_data": "admin:approve"},
    ]
