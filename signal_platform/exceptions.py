"""Custom exceptions used by platform service and API layers."""

from __future__ import annotations


class PlatformError(Exception):
    """Base platform exception."""


class AuthenticationError(PlatformError):
    """Raised when authentication fails."""


class AuthorizationError(PlatformError):
    """Raised when a user lacks access rights."""


class NotFoundError(PlatformError):
    """Raised when an entity cannot be found."""


class ValidationError(PlatformError):
    """Raised when input validation fails."""
