"""Input validation helpers."""

from __future__ import annotations

import re

# Rules:
# - local-part cannot start/end with dot and cannot contain consecutive dots
# - domain must contain at least one dot and end with 2+ alpha TLD chars
_EMAIL_RE = re.compile(
    r"^(?![.])(?!.*[.]{2})[A-Za-z0-9._%+-]+(?<![.])@"
    r"(?![-.])[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return bool(_EMAIL_RE.match(email or ""))


def is_non_empty(value: str) -> bool:
    """Check that a string has non-whitespace content."""
    return bool((value or "").strip())
