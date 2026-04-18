"""
Simple helper to discover TELEGRAM_CHAT_ID from bot updates.

Usage:
  TELEGRAM_BOT_TOKEN=123:abc python examples/telegram_chat_setup.py
"""

import os
import sys

import requests


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Missing TELEGRAM_BOT_TOKEN. Export it first and send a message to your bot.")
        return 1

    base_url = f"https://api.telegram.org/bot{token}"
    try:
        resp = requests.get(f"{base_url}/getUpdates", timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to call Telegram API: {exc}")
        return 1

    data = resp.json()
    updates = data.get("result", [])
    if not updates:
        print("No updates found. Send a message in your target chat/channel, then re-run.")
        return 1

    chat_ids: list[str] = []
    for item in updates:
        msg = item.get("message") or item.get("channel_post") or {}
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is not None:
            value = str(chat_id)
            if value not in chat_ids:
                chat_ids.append(value)

    if not chat_ids:
        print("Updates found, but no chat IDs detected.")
        return 1

    print("Detected chat IDs:")
    for value in chat_ids:
        print(f"  - {value}")
    print("\nUse one of these in .env, for example:")
    print(f"TELEGRAM_CHAT_ID={chat_ids[0]}")
    print("BROADCAST_TELEGRAM_CHANNELS=<optional_comma_separated_ids>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
