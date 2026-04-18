"""Quick health checks for local tbot services."""

from __future__ import annotations

import os
from pathlib import Path
from json import JSONDecodeError

import requests


def _api_base() -> str:
    host = os.getenv("API_HOST", "127.0.0.1")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = os.getenv("API_PORT", "8000")
    return f"http://{host}:{port}"


def main() -> int:
    failures = 0
    print("=== TBOT HEALTH CHECK ===")

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        print("OK   .env file present")
    else:
        print("WARN .env file missing")
        failures += 1

    try:
        resp = requests.get(f"{_api_base()}/api/health", timeout=5)
        try:
            payload = resp.json()
        except JSONDecodeError:
            payload = {}
        if resp.status_code == 200:
            print(f"OK   API health reachable ({payload.get('status', 'ok')})")
        else:
            print(f"WARN API health returned HTTP {resp.status_code}")
            failures += 1
    except requests.RequestException as exc:
        print(f"WARN API health not reachable: {exc}")
        failures += 1

    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if token and ":" in token:
        print("OK   TELEGRAM_BOT_TOKEN format looks valid")
    else:
        print("WARN TELEGRAM_BOT_TOKEN missing or invalid format")
        failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
