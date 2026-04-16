"""CLI entrypoint for the main signal bot workflows."""

from __future__ import annotations

import argparse

from bots.bot_main.handlers import (
    handle_help,
    handle_market,
    handle_performance,
    handle_signals,
    handle_start,
)
from signal_platform.models import get_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Main Signal Bot helper")
    parser.add_argument("--command", choices=["start", "market", "signals", "performance", "help"], default="start")
    args = parser.parse_args()

    if args.command in {"start", "help", "market"}:
        if args.command == "start":
            print(handle_start())
        elif args.command == "help":
            print(handle_help())
        else:
            print(handle_market())
        return

    db = get_session()
    try:
        if args.command == "signals":
            print(handle_signals(db))
        else:
            print(handle_performance(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
