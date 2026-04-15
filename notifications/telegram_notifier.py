"""
Telegram notification module.
Sends signal alerts, performance reports, and error notifications
via the Telegram Bot API.
"""

import logging
from datetime import datetime, timezone

import requests

from config.settings import Settings

logger = logging.getLogger("trading_bot.telegram_notifier")


class TelegramNotifier:
    """Send messages to a Telegram chat via the Bot API."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
    ) -> None:
        self.token = token or Settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or Settings.TELEGRAM_CHAT_ID
        self.api_url = self.BASE_URL.format(token=self.token)
        self.enabled = bool(self.token and self.chat_id)
        if not self.enabled:
            logger.warning("Telegram notifier disabled – token or chat_id missing")

    # ── Low-level send ──────────────────────────────────────────────────

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a text message to the configured chat."""
        if not self.enabled:
            logger.debug("Telegram disabled – message not sent")
            return False

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.info("Telegram message sent")
            return True
        except requests.RequestException as exc:
            logger.error("Telegram send failed: %s", exc)
            return False

    # ── Signal alert ────────────────────────────────────────────────────

    def send_signal(self, signal) -> bool:
        """Format and send a trading signal."""
        emoji = "\U0001f680" if signal.direction == "BUY" else "\U0001f534"
        text = (
            f"{emoji} <b>TRADING SIGNAL</b>\n\n"
            f"<b>Pair:</b> {signal.pair}\n"
            f"<b>Direction:</b> {signal.direction}\n"
            f"<b>Entry:</b> {signal.entry_price:,.4f}\n\n"
            f"<b>Targets:</b>\n"
            f"  TP1: {signal.take_profit_1:,.4f}\n"
            f"  TP2: {signal.take_profit_2:,.4f}\n"
            f"  TP3: {signal.take_profit_3:,.4f}\n\n"
            f"<b>Stop Loss:</b> {signal.stop_loss:,.4f}\n"
            f"<b>Confidence:</b> {signal.confidence:.0%}\n"
            f"<b>Trend:</b> {signal.trend}\n\n"
            f"<b>Reason:</b> {'; '.join(signal.reasons)}\n"
            f"\n<i>{datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}</i>"
        )
        return self.send_message(text)

    # ── Performance report ──────────────────────────────────────────────

    def send_performance_report(
        self,
        total_trades: int,
        win_rate: float,
        total_pnl: float,
        sharpe: float | None = None,
        max_dd: float | None = None,
    ) -> bool:
        """Send a periodic performance summary."""
        text = (
            "\U0001f4ca <b>PERFORMANCE REPORT</b>\n\n"
            f"<b>Total Trades:</b> {total_trades}\n"
            f"<b>Win Rate:</b> {win_rate:.1%}\n"
            f"<b>Total PnL:</b> ${total_pnl:,.2f}\n"
        )
        if sharpe is not None:
            text += f"<b>Sharpe Ratio:</b> {sharpe:.2f}\n"
        if max_dd is not None:
            text += f"<b>Max Drawdown:</b> {max_dd:.1%}\n"
        text += f"\n<i>{datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}</i>"
        return self.send_message(text)

    # ── Error notification ──────────────────────────────────────────────

    def send_error(self, error_msg: str) -> bool:
        """Notify about an error or critical event."""
        text = (
            "\u26a0\ufe0f <b>BOT ERROR</b>\n\n"
            f"<code>{error_msg}</code>\n"
            f"\n<i>{datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}</i>"
        )
        return self.send_message(text)
