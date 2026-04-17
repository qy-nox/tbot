"""Async Telegram entrypoint for the admin bot."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
except ModuleNotFoundError as exc:  # pragma: no cover - import-time fallback
    InlineKeyboardButton = InlineKeyboardMarkup = Update = Any
    Application = CallbackQueryHandler = CommandHandler = ContextTypes = Any
    _TELEGRAM_IMPORT_ERROR = exc
else:
    _TELEGRAM_IMPORT_ERROR = None

logger = logging.getLogger(__name__)


def _ensure_telegram_dependency() -> None:
    if _TELEGRAM_IMPORT_ERROR is not None:
        raise RuntimeError(
            "python-telegram-bot is required to run bots.bot_admin.main; install dependencies from requirements.txt"
        ) from _TELEGRAM_IMPORT_ERROR


def _require_token() -> str | None:
    token = os.getenv("TELEGRAM_BOT_TOKEN_ADMIN") or os.getenv("BOT2_ADMIN_TOKEN")
    if not token or ":" not in token:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN_ADMIN not configured - bot disabled")
        return None
    return token


def _admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_USER_IDS") or os.getenv("ADMIN_IDS") or ""
    parsed: set[int] = set()
    for value in raw.split(","):
        value = value.strip()
        if value.isdigit():
            parsed.add(int(value))
    return parsed


def _admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💳 Payments", callback_data="payments"), InlineKeyboardButton("👥 Users", callback_data="users")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats"), InlineKeyboardButton("👥 Groups", callback_data="groups")],
        ]
    )


class AdminBot:
    def __init__(self) -> None:
        self.allowed_admins = _admin_ids()

    def _is_admin(self, update: Update) -> bool:
        user = update.effective_user
        return bool(user and user.id in self.allowed_admins)

    async def _forbidden(self, update: Update) -> None:
        await update.effective_message.reply_text("Unauthorized")

    async def admin_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_admin.handlers import handle_admin

        if not self._is_admin(update):
            await self._forbidden(update)
            return
        payload = handle_admin()
        await update.effective_message.reply_text(str(payload["text"]), reply_markup=_admin_keyboard())

    async def groups_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_admin.handlers import handle_groups

        if not self._is_admin(update):
            await self._forbidden(update)
            return
        await update.effective_message.reply_text(handle_groups(), reply_markup=_admin_keyboard())

    async def payments_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_admin.handlers import handle_payments
        from signal_platform.models import get_session

        if not self._is_admin(update):
            await self._forbidden(update)
            return
        db = get_session()
        try:
            text = handle_payments(db)
        finally:
            db.close()
        await update.effective_message.reply_text(text, reply_markup=_admin_keyboard())

    async def users_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_admin.handlers import handle_users
        from signal_platform.models import get_session

        if not self._is_admin(update):
            await self._forbidden(update)
            return
        db = get_session()
        try:
            text = handle_users(db)
        finally:
            db.close()
        await update.effective_message.reply_text(text, reply_markup=_admin_keyboard())

    async def stats_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_admin.handlers import handle_stats
        from signal_platform.models import get_session

        if not self._is_admin(update):
            await self._forbidden(update)
            return
        db = get_session()
        try:
            stats = handle_stats(db)
        finally:
            db.close()
        msg = (
            f"Signals: {stats.get('total_signals', 0)}\n"
            f"Wins: {stats.get('wins', 0)}\n"
            f"Losses: {stats.get('losses', 0)}\n"
            f"Win Rate: {stats.get('win_rate', 0)}%"
        )
        await update.effective_message.reply_text(msg, reply_markup=_admin_keyboard())

    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.callback_query.answer()
        data = (update.callback_query.data or "").strip()
        if data == "payments":
            await self.payments_cmd(update, context)
        elif data == "users":
            await self.users_cmd(update, context)
        elif data == "stats":
            await self.stats_cmd(update, context)
        elif data == "groups":
            await self.groups_cmd(update, context)


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
    bot = AdminBot()

    app.add_handler(CommandHandler("admin", bot.admin_cmd))
    app.add_handler(CommandHandler("payments", bot.payments_cmd))
    app.add_handler(CommandHandler("users", bot.users_cmd))
    app.add_handler(CommandHandler("stats", bot.stats_cmd))
    app.add_handler(CommandHandler("groups", bot.groups_cmd))
    app.add_handler(CallbackQueryHandler(bot.callback))

    logger.info("Starting admin bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
