"""Bot-specific environment configuration."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _parse_admin_ids(raw: str) -> tuple[int, ...]:
    ids: list[int] = []
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            ids.append(int(value))
        except ValueError:
            logger.warning("Ignoring invalid ADMIN_USER_IDS value: %s", value)
            continue
    return tuple(ids)


@dataclass(frozen=True)
class BotConfig:
    bot1_token: str = os.getenv("TELEGRAM_TOKEN_BOT1", "")
    bot2_token: str = os.getenv("TELEGRAM_TOKEN_BOT2", "")
    bot3_token: str = os.getenv("TELEGRAM_TOKEN_BOT3", "")
    admin_user_ids: tuple[int, ...] = _parse_admin_ids(os.getenv("ADMIN_USER_IDS", ""))


bot_config = BotConfig()
