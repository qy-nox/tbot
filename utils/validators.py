"""Input validation helpers."""

from __future__ import annotations

import re
from typing import Iterable

# Rules:
# - local-part cannot start/end with dot and cannot contain consecutive dots
# - domain must contain at least one dot and end with 2+ alpha TLD chars
_EMAIL_RE = re.compile(
    r"^(?![.])(?!.*[.]{2})[A-Za-z0-9._%+-]+(?<![.])@"
    r"(?![-.])[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)
_PAIR_RE = re.compile(r"^[A-Z0-9]{2,15}/[A-Z0-9]{2,15}$")


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return bool(_EMAIL_RE.match(email or ""))


def is_non_empty(value: str) -> bool:
    """Check that a string has non-whitespace content."""
    return bool((value or "").strip())


def is_valid_trading_pair(pair: str) -> bool:
    """Validate trading pair symbol format (e.g. BTC/USDT)."""
    return bool(_PAIR_RE.match((pair or "").strip().upper()))


def validate_required_columns(columns: Iterable[str], required: Iterable[str]) -> None:
    """Raise ValueError when required columns are missing."""
    missing = [c for c in required if c not in set(columns)]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
