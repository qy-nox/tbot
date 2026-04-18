"""Interactive wizard to configure Telegram signal group IDs in .env."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
GROUP_SLOTS = [
    ("SIGNAL_GROUP_1_ID", "Crypto B Grade High Volume"),
    ("SIGNAL_GROUP_2_ID", "Crypto B Grade VIP"),
    ("SIGNAL_GROUP_3_ID", "Crypto A Grade High Volume"),
    ("SIGNAL_GROUP_4_ID", "Crypto A Grade VIP"),
    ("SIGNAL_GROUP_5_ID", "Crypto A+ Grade High Volume"),
    ("SIGNAL_GROUP_6_ID", "Crypto A+ Grade VIP"),
    ("SIGNAL_GROUP_7_ID", "Binary B Grade High Volume"),
    ("SIGNAL_GROUP_8_ID", "Binary B Grade VIP"),
    ("SIGNAL_GROUP_9_ID", "Binary A Grade High Volume"),
    ("SIGNAL_GROUP_10_ID", "Binary A Grade VIP"),
    ("SIGNAL_GROUP_11_ID", "Binary A+ Grade High Volume"),
    ("SIGNAL_GROUP_12_ID", "Binary A+ Grade VIP"),
]

PLACEHOLDER_GROUP_IDS = {"-1001234567890", "-1001234567891"}


def is_valid_telegram_chat_id(chat_id: str | None) -> bool:
    if chat_id is None:
        return False
    return bool(re.fullmatch(r"-?\\d+", str(chat_id).strip()))


def is_placeholder_telegram_group_id(chat_id: str | None) -> bool:
    if chat_id is None:
        return False
    return str(chat_id).strip() in PLACEHOLDER_GROUP_IDS


def _load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _save_env_values(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    applied: set[str] = set()
    out: list[str] = []
    for line in lines:
        if "=" not in line or line.lstrip().startswith("#"):
            out.append(line)
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            applied.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in applied:
            out.append(f"{key}={value}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _api_get(token: str, method: str, **params) -> dict:
    query = urlencode(params)
    url = f"https://api.telegram.org/bot{token}/{method}"
    if query:
        url = f"{url}?{query}"
    with urlopen(url, timeout=15) as response:  # nosec - Telegram endpoint
        return json.loads(response.read().decode("utf-8"))


def _verify_group(token: str, group_id: str) -> tuple[bool, str]:
    try:
        payload = _api_get(token, "getChat", chat_id=group_id)
    except Exception as exc:  # pragma: no cover - network/runtime errors
        return False, str(exc)
    if payload.get("ok") is True:
        title = payload.get("result", {}).get("title") or payload.get("result", {}).get("username") or "OK"
        return True, str(title)
    return False, str(payload.get("description", "unknown error"))


def main() -> None:
    env = _load_env_file(ENV_PATH)
    token = os.getenv("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN", "")

    print("Telegram Group Setup Wizard")
    print("- Create groups first")
    print("- Add bot as admin in each group")
    print("- Group IDs must be numeric, usually like -1001234567890\n")

    updates: dict[str, str] = {}
    for key, label in GROUP_SLOTS:
        current = env.get(key, "")
        prompt = f"{label} ({key})"
        if current:
            prompt += f" [current: {current}]"
        prompt += ": "

        while True:
            value = input(prompt).strip()
            if not value:
                value = current
            if not value:
                updates[key] = ""
                break
            if not is_valid_telegram_chat_id(value):
                print("  Invalid format. Expected numeric ID like -1001234567890")
                continue
            if is_placeholder_telegram_group_id(value):
                print("  Placeholder ID detected. Use a real Telegram group ID.")
                continue
            if token:
                ok, details = _verify_group(token, value)
                if ok:
                    print(f"  Verified: {details}")
                else:
                    print(f"  Warning: unable to verify now ({details})")
            updates[key] = value
            break

    _save_env_values(ENV_PATH, updates)
    print(f"\nSaved group configuration to {ENV_PATH}")
    print("Run: python scripts/verify_groups.py")


if __name__ == "__main__":
    main()
