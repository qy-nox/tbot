"""Bot-specific environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    bot1_token: str = os.getenv("TELEGRAM_TOKEN_BOT1", "")
    bot2_token: str = os.getenv("TELEGRAM_TOKEN_BOT2", "")
    bot3_token: str = os.getenv("TELEGRAM_TOKEN_BOT3", "")
    admin_user_ids: tuple[int, ...] = tuple(
        int(x.strip())
        for x in os.getenv("ADMIN_USER_IDS", "").split(",")
        if x.strip().isdigit()
    )


bot_config = BotConfig()
