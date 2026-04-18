"""Entry point for admin bot (compatibility-safe implementation)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def main() -> None:
    """Start admin bot process in compatibility mode."""
    logger.info("Admin bot compatibility entrypoint ready. Use dashboard /admin/ for web controls.")


if __name__ == "__main__":
    main()
