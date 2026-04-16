"""Advanced Telegram notification helpers."""

from __future__ import annotations

from notifications.telegram_notifier import TelegramNotifier


class AdvancedTelegramNotifier(TelegramNotifier):
    def format_with_actions(self, title: str, body: str) -> str:
        return f"{title}\n\n{body}\n\n[Open Dashboard] [Manage Alerts]"
