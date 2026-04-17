"""Core domain exceptions."""

from __future__ import annotations


class TBotError(Exception):
    """Base exception for core bot runtime errors."""


class ValidationError(TBotError):
    """Raised when untrusted input fails validation."""


class SecurityError(TBotError):
    """Raised for security policy violations."""


class ExternalServiceError(TBotError):
    """Raised when upstream providers fail repeatedly."""
