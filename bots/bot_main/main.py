"""Async Telegram entrypoint for the main signal bot."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.error import NetworkError, TimedOut
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
except ModuleNotFoundError as exc:  # pragma: no cover - import-time fallback
    InlineKeyboardButton = InlineKeyboardMarkup = Update = Any
    NetworkError = TimedOut = Exception
    Application = CallbackQueryHandler = CommandHandler = ContextTypes = Any
    _TELEGRAM_IMPORT_ERROR = exc
else:
    _TELEGRAM_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


def _ensure_telegram_dependency() -> None:
    if _TELEGRAM_IMPORT_ERROR is not None:
        raise RuntimeError(
            "python-telegram-bot is required to run bots.bot_main.main; install dependencies from requirements.txt"
        ) from _TELEGRAM_IMPORT_ERROR


def _require_token() -> str | None:
    token = os.getenv("TELEGRAM_BOT_TOKEN_MAIN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or ":" not in token:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN_MAIN not configured - bot disabled")
        return None
    return token


def _main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📊 Market", callback_data="market"), InlineKeyboardButton("🔔 Signals", callback_data="signals")],
            [InlineKeyboardButton("📈 Performance", callback_data="performance"), InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        ]
    )


def _format_market() -> str:
    from bots.bot_main.handlers import handle_market

    market = handle_market()
    assets = "\n".join(f"• {symbol}: {payload.get('price', '-')}" for symbol, payload in market.get("assets", {}).items())
    return f"📊 <b>Market Status</b>\n{assets}\n\nTrend: <b>{market.get('trend', 'N/A')}</b>"


def _format_performance(data: dict[str, object]) -> str:
    return (
        "📈 <b>Performance</b>\n"
        f"Signals: {data.get('total_signals', 0)}\n"
        f"Wins: {data.get('wins', 0)}\n"
        f"Losses: {data.get('losses', 0)}\n"
        f"Win Rate: {data.get('win_rate', 0)}%"
    )


class MainSignalBot:
    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_main.handlers import handle_start

        payload = handle_start()
        await update.effective_message.reply_text(str(payload["text"]), reply_markup=_main_menu())

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_main.handlers import handle_help

        await update.effective_message.reply_text(handle_help())

    async def market_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = _format_market()
        if update.callback_query is not None:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=_main_menu())
            return
        await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=_main_menu())

    async def signals_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_main.handlers import handle_signals
        from signal_platform.models import get_session

        db = get_session()
        try:
            text = handle_signals(db)
        finally:
            db.close()
        if update.callback_query is not None:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, reply_markup=_main_menu())
            return
        await update.effective_message.reply_text(text, reply_markup=_main_menu())

    async def performance_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_main.handlers import handle_performance
        from signal_platform.models import get_session

        db = get_session()
        try:
            text = _format_performance(handle_performance(db))
        finally:
            db.close()
        if update.callback_query is not None:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=_main_menu())
            return
        await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=_main_menu())

    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        action = (update.callback_query.data or "").strip()
        if action == "market":
            await self.market_cmd(update, context)
        elif action == "signals":
            await self.signals_cmd(update, context)
        elif action == "performance":
            await self.performance_cmd(update, context)
        else:
            await self.help_cmd(update, context)


def main() -> None:
    _ensure_telegram_dependency()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    token = _require_token()
    if not token:
        logger.warning("Bot cannot start without token - keeping process alive")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Bot process terminated")
        return

    app = Application.builder().token(token).build()
    bot = MainSignalBot()

    app.add_handler(CommandHandler("start", bot.start_cmd))
    app.add_handler(CommandHandler("help", bot.help_cmd))
    app.add_handler(CommandHandler("market", bot.market_cmd))
    app.add_handler(CommandHandler("signals", bot.signals_cmd))
    app.add_handler(CommandHandler("performance", bot.performance_cmd))
    app.add_handler(CallbackQueryHandler(bot.callback))

    logger.info("Starting main signal bot")
    max_attempts = max(1, int(os.getenv("TELEGRAM_RETRY_ATTEMPTS", "3")))
    base_backoff = max(0.1, float(os.getenv("TELEGRAM_RETRY_BACKOFF_SECONDS", "0.5")))
    max_backoff = max(base_backoff, float(os.getenv("TELEGRAM_RETRY_MAX_BACKOFF_SECONDS", "8.0")))

    for attempt in range(1, max_attempts + 1):
        try:
            app.run_polling(allowed_updates=Update.ALL_TYPES)
            return
        except (TimedOut, NetworkError) as exc:
            if attempt >= max_attempts:
                logger.error("Main signal bot stopped after repeated Telegram timeouts: %s", exc)
                raise
            delay = min(base_backoff * (2 ** (attempt - 1)), max_backoff)
            logger.warning(
                "Telegram polling timeout/network error (attempt %d/%d): %s. Retrying in %.1fs",
                attempt,
                max_attempts,
                exc,
                delay,
            )
            time.sleep(delay)


if __name__ == "__main__":
    main()
