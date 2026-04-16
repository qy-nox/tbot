"""Async Telegram entrypoint for the subscription bot."""

from __future__ import annotations

import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


def _require_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN_SUB") or os.getenv("BOT1_SUBSCRIPTION_TOKEN")
    if not token or ":" not in token:
        raise RuntimeError("Missing or invalid TELEGRAM_BOT_TOKEN_SUB")
    return token


def _plans_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Free", callback_data="sub:free"), InlineKeyboardButton("Premium", callback_data="sub:premium")],
            [InlineKeyboardButton("VIP", callback_data="sub:vip")],
            [InlineKeyboardButton("📄 Plans", callback_data="plans"), InlineKeyboardButton("📌 Status", callback_data="status")],
        ]
    )


class SubscriptionBot:
    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_subscription.handlers import handle_start

        payload = handle_start()
        await update.effective_message.reply_text(str(payload["text"]), reply_markup=_plans_keyboard())

    async def plans_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_subscription.handlers import handle_plans

        payload = handle_plans()
        text = str(payload["text"])
        if update.callback_query is not None:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, reply_markup=_plans_keyboard())
            return
        await update.effective_message.reply_text(text, reply_markup=_plans_keyboard())

    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_subscription.handlers import handle_status

        user_id = update.effective_user.id
        text = handle_status(user_id)
        await update.effective_message.reply_text(text, reply_markup=_plans_keyboard())

    async def billing_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        from bots.bot_subscription.handlers import handle_billing

        user_id = update.effective_user.id
        text = handle_billing(user_id)
        await update.effective_message.reply_text(text, reply_markup=_plans_keyboard())

    async def subscribe_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str) -> None:
        from bots.bot_subscription.handlers import handle_subscribe

        user = update.effective_user
        payload = handle_subscribe(username=user.username or f"user_{user.id}", user_id=user.id, telegram_id=str(user.id), plan=plan)
        message_text = str(payload["text"]) + f"\nSelected plan: {plan.upper()}"
        if update.callback_query is not None:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(message_text, reply_markup=_plans_keyboard())
            return
        await update.effective_message.reply_text(message_text, reply_markup=_plans_keyboard())

    async def subscribe_from_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        plan = (context.args[0].lower() if context.args else "premium").strip()
        if plan not in {"free", "premium", "vip"}:
            await update.effective_message.reply_text("Usage: /subscribe [free|premium|vip]")
            return
        await self.subscribe_cmd(update, context, plan)

    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        data = (update.callback_query.data or "").strip()
        if data == "plans":
            await self.plans_cmd(update, context)
            return
        if data == "status":
            from bots.bot_subscription.handlers import handle_status

            await update.callback_query.answer()
            await update.callback_query.edit_message_text(handle_status(update.effective_user.id), reply_markup=_plans_keyboard())
            return
        if data.startswith("sub:"):
            await self.subscribe_cmd(update, context, data.split(":", 1)[1])
            return
        await update.callback_query.answer()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    app = Application.builder().token(_require_token()).build()
    bot = SubscriptionBot()

    app.add_handler(CommandHandler("start", bot.start_cmd))
    app.add_handler(CommandHandler("plans", bot.plans_cmd))
    app.add_handler(CommandHandler("status", bot.status_cmd))
    app.add_handler(CommandHandler("billing", bot.billing_cmd))
    app.add_handler(CommandHandler("subscribe", bot.subscribe_from_command))
    app.add_handler(CallbackQueryHandler(bot.callback))

    logger.info("Starting subscription bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
