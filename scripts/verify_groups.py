"""Verify configured Telegram signal group IDs and bot access."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import requests

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
GROUP_KEYS = [f"SIGNAL_GROUP_{idx}_ID" for idx in range(1, 13)]
PLACEHOLDER_GROUP_IDS = {"-1001234567890", "-1001234567891"}


def is_valid_telegram_chat_id(chat_id: str | None) -> bool:
    if chat_id is None:
        return False
    return bool(re.fullmatch(r"-?\d+", str(chat_id).strip()))


def is_placeholder_telegram_group_id(chat_id: str | None) -> bool:
    if chat_id is None:
        return False
    return str(chat_id).strip() in PLACEHOLDER_GROUP_IDS


def _load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _api_get(token: str, method: str, **params) -> dict:
    response = requests.get(
        f"https://api.telegram.org/bot{token}/{method}",
        params=params,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def _api_post(token: str, method: str, payload: dict) -> dict:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/{method}",
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Telegram signal groups")
    parser.add_argument("--send-test", action="store_true", help="Send test message to each verified group")
    args = parser.parse_args()

    env = _load_env(ENV_PATH)
    token = os.getenv("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN missing in environment/.env")
        return 1

    ids = [env.get(key, "").strip() for key in GROUP_KEYS]
    configured = [(key, value) for key, value in zip(GROUP_KEYS, ids) if value]
    if not configured:
        print("ERROR: no SIGNAL_GROUP_*_ID values configured")
        return 1

    failures = 0
    for key, group_id in configured:
        if not is_valid_telegram_chat_id(group_id):
            print(f"{key}: INVALID_FORMAT ({group_id})")
            failures += 1
            continue
        if is_placeholder_telegram_group_id(group_id):
            print(f"{key}: PLACEHOLDER_ID ({group_id})")
            failures += 1
            continue

        try:
            chat = _api_get(token, "getChat", chat_id=group_id)
        except requests.RequestException as exc:  # pragma: no cover - network/runtime errors
            print(f"{key}: VERIFY_ERROR ({exc})")
            failures += 1
            continue

        if chat.get("ok") is not True:
            print(f"{key}: NOT_ACCESSIBLE ({chat.get('description', 'unknown')})")
            failures += 1
            continue

        title = chat.get("result", {}).get("title") or chat.get("result", {}).get("username") or "(unknown)"
        print(f"{key}: OK ({title})")

        if args.send_test:
            try:
                result = _api_post(
                    token,
                    "sendMessage",
                    {
                        "chat_id": group_id,
                        "text": "✅ TBOT group verification successful.",
                    },
                )
                if result.get("ok") is True:
                    print(f"  test: sent")
                else:
                    print(f"  test: failed ({result.get('description', 'unknown')})")
                    failures += 1
            except requests.RequestException as exc:  # pragma: no cover - network/runtime errors
                print(f"  test: error ({exc})")
                failures += 1

    if failures:
        print(f"\nVerification completed with {failures} problem(s).")
        return 1

    print("\nAll configured groups verified successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
