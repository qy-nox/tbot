"""Entry point for subscription/payment bot."""

from __future__ import annotations

from bots.bot_subscription.main import main as run


def main() -> None:
    """Run subscription bot."""
    run()


if __name__ == "__main__":
    main()
