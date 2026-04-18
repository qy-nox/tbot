"""Entry point for the production-style main signal bot."""

from __future__ import annotations

from bots.bot_main.main import main as run


def main() -> None:
    """Run the main signal bot."""
    run()


if __name__ == "__main__":
    main()
