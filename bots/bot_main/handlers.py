"""Command handlers for the main signal bot."""

from __future__ import annotations

from signal_platform.models import SignalOutcome, SignalRecord, get_session
from signal_platform.services.performance_service import PerformanceService

from bots.bot_main.keyboard import main_menu_keyboard
from bots.bot_main.market_data import get_live_market_status
from bots.bot_main.signal_display import format_signal_list


def handle_start() -> dict[str, object]:
    return {
        "text": "Welcome to the Main Signal Bot! Use /market /signals /performance /help",
        "keyboard": main_menu_keyboard(),
    }


def handle_help() -> str:
    return "Commands: /start /market /signals /performance /help"


def handle_market() -> dict[str, object]:
    return get_live_market_status()


def handle_signals(db, *, limit: int = 10) -> str:
    """Fetch pending signals and return Telegram-formatted output."""
    active = (
        db.query(SignalRecord)
        .filter(SignalRecord.outcome == SignalOutcome.PENDING)
        .filter(SignalRecord.approved == True)
        .order_by(SignalRecord.timestamp.desc())
        .limit(limit)
        .all()
    )
    return format_signal_list(active)


def handle_performance(db) -> dict[str, float | int | None]:
    return PerformanceService.overview(db)
