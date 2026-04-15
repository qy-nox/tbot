"""
Multi-channel signal distribution with retry support.

Channels
--------
- Telegram (groups & channels)
- Discord (webhook)
- Email (SMTP)
- WhatsApp (placeholder – requires business API)
- API (WebSocket / polling – handled by the REST layer)
"""

from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import List, Optional

import aiohttp
from sqlalchemy.orm import Session

from signal_platform.models import (
    DeliveryChannel,
    DeliveryStatus,
    SignalDelivery,
    SignalRecord,
    SignalType,
    SubscriptionTier,
    User,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

# ── Telegram config ─────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ── Discord config ──────────────────────────────────────────────────────

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# ── Email config ────────────────────────────────────────────────────────

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "signals@tradingbot.com")


class DistributionService:
    """Distribute signals to users across all configured channels."""

    # ── Main distribution entry point ───────────────────────────────────

    @staticmethod
    def distribute(db: Session, signal: SignalRecord) -> List[SignalDelivery]:
        """Send *signal* to all eligible users via their preferred channels."""
        users = _eligible_users(db, signal)
        deliveries: List[SignalDelivery] = []

        for user in users:
            for channel, target in _user_channels(user):
                delivery = SignalDelivery(
                    signal_id=signal.id,
                    user_id=user.id,
                    channel=channel,
                    channel_target=target,
                )
                db.add(delivery)
                db.flush()
                deliveries.append(delivery)

        # Also send to configured broadcast channels (no user)
        for channel, target in _broadcast_targets():
            delivery = SignalDelivery(
                signal_id=signal.id,
                channel=channel,
                channel_target=target,
            )
            db.add(delivery)
            db.flush()
            deliveries.append(delivery)

        db.commit()

        # Attempt delivery
        message = _format_signal(signal)
        for d in deliveries:
            _send(db, d, message)

        return deliveries

    # ── Retry failed deliveries ─────────────────────────────────────────

    @staticmethod
    def retry_failed(db: Session) -> int:
        """Retry deliveries that have failed but haven't exceeded MAX_RETRIES."""
        pending = (
            db.query(SignalDelivery)
            .filter(
                SignalDelivery.status.in_([
                    DeliveryStatus.FAILED,
                    DeliveryStatus.RETRYING,
                ]),
                SignalDelivery.retry_count < MAX_RETRIES,
            )
            .all()
        )
        count = 0
        for d in pending:
            sig = db.query(SignalRecord).get(d.signal_id)
            if sig is None:
                continue
            message = _format_signal(sig)
            d.status = DeliveryStatus.RETRYING
            d.retry_count += 1
            db.commit()
            _send(db, d, message)
            count += 1
        return count

    # ── Delivery status listing ─────────────────────────────────────────

    @staticmethod
    def delivery_status(
        db: Session, signal_id: int
    ) -> List[SignalDelivery]:
        return (
            db.query(SignalDelivery)
            .filter(SignalDelivery.signal_id == signal_id)
            .all()
        )


# ── Internal helpers ────────────────────────────────────────────────────


def _eligible_users(db: Session, signal: SignalRecord) -> List[User]:
    """Return users whose subscription allows them to receive this signal."""
    q = db.query(User).filter(User.is_active.is_(True))
    # Free users only get grade A+ / A crypto signals
    # Premium users get A+, A, B
    # VIP users get everything
    users = q.all()
    eligible: list[User] = []
    for u in users:
        if _can_receive(u, signal):
            eligible.append(u)
    return eligible


def _can_receive(user: User, signal: SignalRecord) -> bool:
    tier = user.subscription_tier
    grade = signal.grade

    if tier == SubscriptionTier.VIP:
        return True

    if tier == SubscriptionTier.PREMIUM:
        if signal.signal_type == SignalType.BINARY:
            return True
        return grade in (None, "A+", "A", "B")  # type: ignore[comparison-overlap]

    # Free
    if signal.signal_type == SignalType.BINARY:
        return False
    return grade in (None, "A+", "A")  # type: ignore[comparison-overlap]


def _user_channels(user: User) -> list[tuple[DeliveryChannel, str]]:
    channels: list[tuple[DeliveryChannel, str]] = []
    if user.telegram_chat_id:
        channels.append((DeliveryChannel.TELEGRAM, user.telegram_chat_id))
    if user.discord_user_id:
        channels.append((DeliveryChannel.DISCORD, user.discord_user_id))
    if user.whatsapp_number:
        channels.append((DeliveryChannel.WHATSAPP, user.whatsapp_number))
    if user.email:
        channels.append((DeliveryChannel.EMAIL, user.email))
    return channels


def _broadcast_targets() -> list[tuple[DeliveryChannel, str]]:
    """Return non-user broadcast targets from environment."""
    targets: list[tuple[DeliveryChannel, str]] = []
    tg_channels = os.getenv("BROADCAST_TELEGRAM_CHANNELS", "")
    for ch in tg_channels.split(","):
        ch = ch.strip()
        if ch:
            targets.append((DeliveryChannel.TELEGRAM, ch))
    if DISCORD_WEBHOOK_URL:
        targets.append((DeliveryChannel.DISCORD, DISCORD_WEBHOOK_URL))
    return targets


def _format_signal(sig: SignalRecord) -> str:
    """Build a human-readable signal message."""
    if sig.signal_type == SignalType.BINARY:
        return _format_binary_signal(sig)
    return _format_crypto_signal(sig)


def _format_crypto_signal(sig: SignalRecord) -> str:
    grade_str = f" [{sig.grade.value}]" if sig.grade else ""
    lines = [
        f"🚀 CRYPTO TRADING SIGNAL{grade_str}",
        "",
        f"Pair: {sig.pair}",
        f"Direction: {sig.direction.value}",
        f"Entry: ${sig.entry_price:,.2f}",
        "",
        "Targets:",
    ]
    if sig.take_profit_1:
        lines.append(f"├─ TP1: ${sig.take_profit_1:,.2f}")
    if sig.take_profit_2:
        lines.append(f"├─ TP2: ${sig.take_profit_2:,.2f}")
    if sig.take_profit_3:
        lines.append(f"└─ TP3: ${sig.take_profit_3:,.2f}")
    if sig.stop_loss:
        lines.append(f"\nStop Loss: ${sig.stop_loss:,.2f}")
    if sig.risk_reward_ratio:
        lines.append(f"R/R Ratio: 1:{sig.risk_reward_ratio:.1f}")
    lines.append(f"\nConfidence: {sig.confidence * 100:.0f}%")
    if sig.reason:
        lines.append(f"Reason: {sig.reason}")
    if sig.valid_until:
        lines.append(f"Valid Until: {sig.valid_until:%Y-%m-%d %H:%M} UTC")
    return "\n".join(lines)


def _format_binary_signal(sig: SignalRecord) -> str:
    grade_str = f" [{sig.grade.value}]" if sig.grade else ""
    direction_emoji = "🟢" if sig.binary_direction == "CALL" else "🔴"
    duration = sig.binary_duration or 60
    if duration >= 60:
        dur_str = f"{duration // 60} min"
    else:
        dur_str = f"{duration} sec"
    lines = [
        f"⚡ BINARY TRADING SIGNAL{grade_str}",
        "",
        f"Pair: {sig.pair}",
        f"Direction: {direction_emoji} {sig.binary_direction or sig.direction.value}",
        f"Entry: ${sig.entry_price:,.2f}",
        f"Duration: {dur_str}",
        f"\nConfidence: {sig.confidence * 100:.0f}%",
    ]
    if sig.reason:
        lines.append(f"Reason: {sig.reason}")
    if sig.valid_until:
        lines.append(f"Valid Until: {sig.valid_until:%Y-%m-%d %H:%M} UTC")
    return "\n".join(lines)


# ── Channel senders ─────────────────────────────────────────────────────


def _send(db: Session, delivery: SignalDelivery, message: str) -> None:
    try:
        if delivery.channel == DeliveryChannel.TELEGRAM:
            _send_telegram(delivery.channel_target, message)
        elif delivery.channel == DeliveryChannel.DISCORD:
            _send_discord(delivery.channel_target, message)
        elif delivery.channel == DeliveryChannel.EMAIL:
            _send_email(delivery.channel_target, message)
        elif delivery.channel == DeliveryChannel.WHATSAPP:
            logger.info("WhatsApp delivery not yet implemented (target=%s)", delivery.channel_target)
        # Mark success
        delivery.status = DeliveryStatus.SENT
        delivery.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        delivery.status = DeliveryStatus.FAILED
        delivery.error_message = str(exc)[:500]
        logger.warning("Delivery #%d failed: %s", delivery.id, exc)
    finally:
        db.commit()


def _send_telegram(chat_id: str, text: str) -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")

    loop = _get_or_create_event_loop()
    loop.run_until_complete(_async_send_telegram(chat_id, text))


async def _async_send_telegram(chat_id: str, text: str) -> None:
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"Telegram API error {resp.status}: {body}")


def _send_discord(webhook_url: str, text: str) -> None:
    if not webhook_url:
        raise RuntimeError("Discord webhook URL not configured")

    loop = _get_or_create_event_loop()
    loop.run_until_complete(_async_send_discord(webhook_url, text))


async def _async_send_discord(webhook_url: str, text: str) -> None:
    payload = {"content": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as resp:
            if resp.status not in (200, 204):
                body = await resp.text()
                raise RuntimeError(f"Discord webhook error {resp.status}: {body}")


def _send_email(to_addr: str, text: str) -> None:
    if not SMTP_USER:
        raise RuntimeError("SMTP not configured")
    msg = MIMEText(text)
    msg["Subject"] = "🚀 New Trading Signal"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_addr
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(EMAIL_FROM, [to_addr], msg.as_string())


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
