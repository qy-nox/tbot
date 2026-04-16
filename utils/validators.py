"""Input validation helpers."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return bool(_EMAIL_RE.match(email or ""))


def is_non_empty(value: str) -> bool:
    """Check that a string has non-whitespace content."""
    return bool((value or "").strip())
