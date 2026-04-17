"""Encryption helpers for sensitive values."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config.settings import Settings


def _build_fernet_key() -> bytes:
    if not Settings.ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY must be configured")
    raw = Settings.ENCRYPTION_KEY.encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)


_FERNET = Fernet(_build_fernet_key())


def encrypt_text(value: str) -> str:
    """Encrypt a plaintext string."""
    return _FERNET.encrypt((value or "").encode("utf-8")).decode("utf-8")


def decrypt_text(value: str) -> str:
    """Decrypt encrypted text."""
    try:
        return _FERNET.decrypt((value or "").encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Invalid encrypted payload") from exc
