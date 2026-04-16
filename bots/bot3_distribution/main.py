"""CLI entrypoint for Bot 3 (distribution)."""

from __future__ import annotations

import argparse

from bots.bot3_distribution.handlers import handle_distribute
from signal_platform.models import SignalRecord, get_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot3 Distribution helper")
    parser.add_argument("--signal-id", type=int, required=True)
    args = parser.parse_args()

    db = get_session()
    try:
        signal = db.get(SignalRecord, args.signal_id)
        ok, message = handle_distribute(db, signal)
        if not ok:
            raise SystemExit(message)
        print(message)
    finally:
        db.close()


if __name__ == "__main__":
    main()
