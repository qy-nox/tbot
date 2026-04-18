"""Group distribution service using 12 managed groups."""

from __future__ import annotations

from bots.main_signal_bot.distribution import target_groups


def select_target_groups(*, signal_type: str, grade: str) -> list[str]:
    return [group.key for group in target_groups(signal_type=signal_type, grade=grade)]
