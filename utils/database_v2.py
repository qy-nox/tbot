"""V2 database bootstrap utilities (legacy + platform tables)."""

from utils.database import init_db as init_legacy_db
from signal_platform.models import init_db as init_platform_db


def init_db() -> None:
    init_legacy_db()
    init_platform_db()
