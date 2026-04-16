"""Signal platform configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlatformSettings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))


settings = PlatformSettings()

if settings.jwt_secret == "change-me-in-production":
    logger.warning("JWT_SECRET is using the default insecure value; set it before production use.")
