"""Runtime diagnostics for common tbot startup issues."""

from __future__ import annotations

import os
import re
import socket
from pathlib import Path
from json import JSONDecodeError

import requests

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
PLACEHOLDER_GROUP_IDS = {"-1001234567890", "-1001234567891"}
SIGNAL_GROUP_COUNT = 12


def _load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def _env_or_file(env_data: dict[str, str], key: str, default: str = "") -> str:
    return (os.getenv(key) or env_data.get(key) or default).strip()


def _is_chat_id(value: str | None) -> bool:
    return bool(value and re.fullmatch(r"-?\d+", str(value).strip()))


def _is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _check_port(host: str, port: int) -> tuple[bool, str]:
    ok = _is_port_available(host, port)
    if ok:
        return True, f"API port {host}:{port} is available"
    return False, f"API port {host}:{port} is busy (run: python scripts/fix_port.py --port {port})"


def _check_network() -> tuple[bool, str]:
    try:
        requests.get("https://api.telegram.org", timeout=5)
        return True, "Telegram API endpoint reachable"
    except requests.RequestException as exc:
        return False, f"Cannot reach Telegram API endpoint: {exc}"


def _check_token(token: str) -> tuple[bool, str]:
    if not token:
        return False, "TELEGRAM_BOT_TOKEN is missing"
    if ":" not in token:
        return False, "TELEGRAM_BOT_TOKEN format is invalid (expected '<id>:<token>')"
    try:
        resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        payload = resp.json()
    except JSONDecodeError:
        payload = {}
    except requests.RequestException as exc:
        message = str(exc)
        if token:
            message = message.replace(token, "***")
        return False, f"Bot token validation failed: {message}"
    if resp.status_code == 200 and isinstance(payload, dict) and payload.get("ok") is True:
        username = payload.get("result", {}).get("username") or "(unknown)"
        return True, f"Bot token is valid (username=@{username})"
    return False, f"Bot token rejected: {payload.get('description', 'unknown error')}"


def _check_groups(token: str, groups: list[str]) -> list[str]:
    messages: list[str] = []
    if not groups:
        messages.append("No SIGNAL_GROUP_*_ID entries configured")
        return messages
    if not token:
        messages.append("Cannot verify groups without TELEGRAM_BOT_TOKEN")
        return messages
    for group_id in groups:
        if not _is_chat_id(group_id):
            messages.append(f"GROUP_INVALID_FORMAT: {group_id}")
            continue
        if group_id in PLACEHOLDER_GROUP_IDS:
            messages.append(f"GROUP_PLACEHOLDER: {group_id}")
            continue
        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{token}/getChat",
                params={"chat_id": group_id},
                timeout=10,
            )
            try:
                payload = resp.json()
            except JSONDecodeError:
                payload = {}
        except requests.RequestException as exc:
            messages.append(f"GROUP_VERIFY_ERROR: {group_id} ({exc})")
            continue
        if resp.status_code == 200 and isinstance(payload, dict) and payload.get("ok") is True:
            title = payload.get("result", {}).get("title") or payload.get("result", {}).get("username") or "OK"
            messages.append(f"GROUP_OK: {group_id} ({title})")
            continue
        description = payload.get("description", "unknown")
        messages.append(f"GROUP_NOT_FOUND: {group_id} ({description})")
    return messages


def main() -> int:
    env_data = _load_env(ENV_PATH)
    host = _env_or_file(env_data, "API_HOST", "0.0.0.0")
    port = int(_env_or_file(env_data, "API_PORT", "8000"))
    token = _env_or_file(env_data, "TELEGRAM_BOT_TOKEN")
    groups = [
        _env_or_file(env_data, f"SIGNAL_GROUP_{idx}_ID")
        for idx in range(1, SIGNAL_GROUP_COUNT + 1)
        if _env_or_file(env_data, f"SIGNAL_GROUP_{idx}_ID")
    ]

    checks = [
        _check_port(host, port),
        _check_network(),
        _check_token(token),
    ]

    failures = 0
    print("=== TBOT DIAGNOSTIC REPORT ===")
    for ok, message in checks:
        print(("OK   " if ok else "FAIL "), message)
        if not ok:
            failures += 1

    for message in _check_groups(token, groups):
        is_ok = message.startswith("GROUP_OK")
        print(("OK   " if is_ok else "WARN "), message)
        if message.startswith(("GROUP_NOT_FOUND", "GROUP_INVALID_FORMAT", "GROUP_PLACEHOLDER")):
            failures += 1

    if failures:
        print("\nSuggested fixes:")
        print("- Run: python scripts/fix_port.py")
        print("- Run: python scripts/verify_groups.py --send-test")
        print("- Check Telegram token and internet connectivity")
        return 1

    print("\nAll diagnostic checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
