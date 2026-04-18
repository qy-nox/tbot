"""Discover Telegram group IDs from bot updates and optionally save to .env."""

from __future__ import annotations

import os
from pathlib import Path

import requests

GROUP_ENV_KEYS = [f"SIGNAL_GROUP_{idx}_ID" for idx in range(1, 13)]
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _save_env_values(path: Path, updates: dict[str, str]) -> None:
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    applied: set[str] = set()
    rendered: list[str] = []
    for line in existing:
        if "=" not in line or line.lstrip().startswith("#"):
            rendered.append(line)
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key in updates:
            rendered.append(f"{key}={updates[key]}")
            applied.add(key)
        else:
            rendered.append(line)
    for key, value in updates.items():
        if key not in applied:
            rendered.append(f"{key}={value}")
    path.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")


def _api_get(token: str, method: str, **params) -> dict:
    response = requests.get(
        f"https://api.telegram.org/bot{token}/{method}",
        params=params,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def _extract_chats(payload: dict) -> list[tuple[str, str]]:
    chats: dict[str, str] = {}
    for item in payload.get("result", []):
        message = item.get("message") or item.get("channel_post") or {}
        chat = message.get("chat") or {}
        if not chat:
            member_change = item.get("my_chat_member") or {}
            chat = member_change.get("chat") or {}
        chat_id = str(chat.get("id", "")).strip()
        chat_type = str(chat.get("type", "")).strip().lower()
        title = str(chat.get("title") or chat.get("username") or chat_id).strip()
        if chat_id and chat_type in {"group", "supergroup", "channel"}:
            chats[chat_id] = title
    return sorted(chats.items(), key=lambda row: row[1].lower())


def main() -> None:
    env_values = _load_env_file(ENV_PATH)
    token = os.getenv("TELEGRAM_BOT_TOKEN") or env_values.get("TELEGRAM_BOT_TOKEN", "")

    print("STEP 1: Create your Telegram groups (12 total).")
    print("STEP 2: Add your bot to every group and grant admin rights.")
    print("STEP 3: Send one message in each group so getUpdates can see it.\n")

    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN missing. Add it to .env first.")
        return

    try:
        updates = _api_get(token, "getUpdates", timeout=30)
    except requests.RequestException as exc:  # pragma: no cover - network/runtime errors
        print(f"ERROR: Failed to call Telegram API: {exc}")
        return

    chats = _extract_chats(updates)
    if not chats:
        print("No Telegram groups found in updates.")
        print("Send a message in each group and run this script again.")
        return

    print("Discovered groups:")
    for idx, (chat_id, title) in enumerate(chats, start=1):
        print(f"  {idx:02d}. {title} -> {chat_id}")

    assignments: dict[str, str] = {}
    for idx, key in enumerate(GROUP_ENV_KEYS):
        if idx < len(chats):
            assignments[key] = chats[idx][0]

    if not assignments:
        print("No SIGNAL_GROUP_* slots to update.")
        return

    answer = input("\nSave discovered IDs to .env SIGNAL_GROUP_1_ID..SIGNAL_GROUP_12_ID? [y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Skipped saving. Copy IDs manually or run scripts/setup_groups_wizard.py.")
        return

    _save_env_values(ENV_PATH, assignments)
    print(f"Saved {len(assignments)} group IDs to {ENV_PATH}")
    print("Next: run python scripts/verify_groups.py")


if __name__ == "__main__":
    main()
