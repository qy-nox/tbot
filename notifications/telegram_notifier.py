"""
Telegram notification module.
Sends signal alerts, performance reports, and error notifications
via the Telegram Bot API.
"""

import logging
import time
from datetime import datetime, timezone

import requests

from config.settings import (
    Settings,
    is_valid_telegram_chat_id,
    is_valid_telegram_token,
)

logger = logging.getLogger("trading_bot.telegram_notifier")


class TelegramNotifier:
    """Send messages to a Telegram chat via the Bot API."""

    BASE_URL = "https://api.telegram.org/bot{token}"
    ERROR_BODY_PREVIEW_LENGTH = 300

    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
    ) -> None:
        self.token = token or Settings.TELEGRAM_BOT_TOKEN
        self.chat_ids = self._resolve_chat_ids(chat_id)
        self.chat_id = self.chat_ids[0] if self.chat_ids else ""
        self.api_url = self.BASE_URL.format(token=self.token) if self.token else ""
        self.enabled = bool(is_valid_telegram_token(self.token) and self.chat_ids)
        if not self.enabled:
            logger.warning(
                "Telegram notifier disabled – invalid token or no valid chat_id configured "
                "(TELEGRAM_CHAT_ID/BROADCAST_TELEGRAM_CHANNELS)"
            )
        else:
            logger.info("Telegram notifier initialised for chat_ids=%s", ",".join(self.chat_ids))

    @staticmethod
    def _resolve_chat_ids(override_chat_id: str | None = None) -> list[str]:
        selected: list[str] = []
        primary = (override_chat_id or Settings.TELEGRAM_CHAT_ID or "").strip()
        if primary:
            if is_valid_telegram_chat_id(primary):
                selected.append(primary)
            else:
                logger.error(
                    "Invalid TELEGRAM_CHAT_ID=%r. Expected numeric chat id like 123456789 or -1001234567890.",
                    primary,
                )

        channels = list(Settings.TELEGRAM_BROADCAST_CHANNELS)
        for channel in channels:
            value = str(channel).strip()
            if not is_valid_telegram_chat_id(value):
                logger.error(
                    "Invalid TELEGRAM_BROADCAST_CHANNELS/BROADCAST_TELEGRAM_CHANNELS entry=%r. "
                    "Expected numeric chat id like 123456789 or -1001234567890.",
                    value,
                )
                continue
            if value not in selected:
                selected.append(value)

        return selected

    # ── Low-level send ──────────────────────────────────────────────────

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a text message to the configured chat."""
        if not self.enabled:
            logger.debug("Telegram disabled – message not sent")
            return False

        url = f"{self.api_url}/sendMessage"
        max_attempts = max(1, Settings.TELEGRAM_RETRY_ATTEMPTS)
        for attempt in range(1, max_attempts + 1):
            sent_any = False
            try:
                for chat_id in self.chat_ids:
                    payload = {
                        "chat_id": chat_id,
                        "text": text,
                    }
                    if parse_mode:
                        payload["parse_mode"] = parse_mode
                    resp = requests.post(url, json=payload, timeout=10)
                    try:
                        resp.raise_for_status()
                        try:
                            data = resp.json() if resp.text else None
                        except ValueError:
                            raise requests.HTTPError("Telegram API returned non-JSON response body", response=resp)
                        if data is None:
                            raise requests.HTTPError(
                                "Telegram API returned empty response body; expected JSON with ok field",
                                response=resp,
                            )
                        if isinstance(data, dict) and data.get("ok") is False:
                            raise requests.HTTPError(
                                f"Telegram API error: {data.get('description', 'unknown')}",
                                response=resp,
                            )
                        sent_any = True
                    except requests.HTTPError:
                        # Retry once without parse_mode for 400 responses; this handles
                        # malformed HTML entity errors while keeping delivery resilient.
                        failed_response = resp
                        body = resp.text[: self.ERROR_BODY_PREVIEW_LENGTH]
                        if parse_mode and getattr(resp, "status_code", None) == 400:
                            fallback_payload = {
                                "chat_id": chat_id,
                                "text": text,
                            }
                            fallback_resp = requests.post(url, json=fallback_payload, timeout=10)
                            try:
                                fallback_resp.raise_for_status()
                                try:
                                    fallback_data = fallback_resp.json() if fallback_resp.text else None
                                except ValueError:
                                    raise requests.HTTPError(
                                        "Telegram API returned non-JSON response body",
                                        response=fallback_resp,
                                    )
                                if fallback_data is None:
                                    raise requests.HTTPError(
                                        "Telegram API returned empty response body; expected JSON with ok field",
                                        response=fallback_resp,
                                    )
                                if isinstance(fallback_data, dict) and fallback_data.get("ok") is False:
                                    raise requests.HTTPError(
                                        f"Telegram API error: {fallback_data.get('description', 'unknown')}",
                                        response=fallback_resp,
                                    )
                                sent_any = True
                                continue
                            except requests.HTTPError:
                                failed_response = fallback_resp
                                body = fallback_resp.text[: self.ERROR_BODY_PREVIEW_LENGTH]
                        logger.error(
                            "Telegram send failed for chat_id=%s (attempt %d/%d): status=%s body=%r",
                            chat_id,
                            attempt,
                            max_attempts,
                            getattr(failed_response, "status_code", "n/a"),
                            body,
                        )
                if sent_any:
                    logger.info("Telegram message sent to %d chat(s)", len(self.chat_ids))
                    return True
            except requests.RequestException as exc:
                logger.error("Telegram send failed (attempt %d/%d): %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                # Linear backoff: 0.5s, 1.0s, 1.5s, ...
                time.sleep(0.5 * attempt)
        return False

    def test_connection(self) -> bool:
        """Validate Telegram token/chat configuration with a lightweight request."""
        if not self.enabled:
            logger.error("Telegram test_connection skipped: notifier disabled (check token/chat_id).")
            return False
        try:
            resp = requests.get(f"{self.api_url}/getMe", timeout=10)
            resp.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.error("Telegram test_connection failed: %s", exc)
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
