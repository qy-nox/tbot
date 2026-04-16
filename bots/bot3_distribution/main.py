"""CLI entrypoint for Bot 3 (distribution)."""

from __future__ import annotations

import argparse

from bots.bot3_distribution.distributor import distribute_signal
from bots.bot3_distribution.signal_validator import is_valid_signal
from signal_platform.models import SignalRecord, get_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot3 Distribution helper")
    parser.add_argument("--signal-id", type=int, required=True)
    args = parser.parse_args()

    db = get_session()
    try:
        signal = db.get(SignalRecord, args.signal_id)
        if not is_valid_signal(signal):
            raise SystemExit("Invalid or missing signal")
        deliveries = distribute_signal(db, signal)
        print(f"Delivered to {len(deliveries)} targets")
    finally:
        db.close()


if __name__ == "__main__":
    main()
