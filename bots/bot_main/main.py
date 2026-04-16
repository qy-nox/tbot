"""Async Telegram entrypoint for the main signal bot."""

from __future__ import annotations

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


def _require_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN_MAIN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or ":" not in token:
        raise RuntimeError("Missing or invalid TELEGRAM_BOT_TOKEN_MAIN")
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
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    app = Application.builder().token(_require_token()).build()
    bot = MainSignalBot()

    app.add_handler(CommandHandler("start", bot.start_cmd))
    app.add_handler(CommandHandler("help", bot.help_cmd))
    app.add_handler(CommandHandler("market", bot.market_cmd))
    app.add_handler(CommandHandler("signals", bot.signals_cmd))
    app.add_handler(CommandHandler("performance", bot.performance_cmd))
    app.add_handler(CallbackQueryHandler(bot.callback))

    logger.info("Starting main signal bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
