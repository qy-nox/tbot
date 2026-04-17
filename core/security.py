"""Security, validation and resilience helpers."""

from __future__ import annotations

import functools
import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any, Callable, TypeVar

from config.settings import Settings
from core.exceptions import ExternalServiceError, ValidationError
from utils.validators import is_valid_trading_pair

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

_SENSITIVE_KEYS = ("api_key", "apikey", "secret", "token", "password", "passphrase")
_RATE_LOCK = threading.Lock()
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def redact_sensitive(text: str) -> str:
    """Mask sensitive key-value pairs in logs."""
    out = text or ""
    for key in _SENSITIVE_KEYS:
        out = out.replace(f"{key}=", f"{key}=***")
        out = out.replace(f"{key.upper()}=", f"{key.upper()}=***")
    return out


def ensure_valid_pair(pair: str) -> str:
    """Validate and normalize trading pair format."""
    normalized = (pair or "").strip().upper()
    if not is_valid_trading_pair(normalized):
        raise ValidationError(f"Invalid trading pair: {pair!r}")
    return normalized


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Retry a function with exponential backoff."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            last_error: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_error = exc
                    if attempt >= max_attempts:
                        break
                    sleep_for = base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Retrying %s after %s (attempt %d/%d)",
                        func.__name__,
                        exc,
                        attempt,
                        max_attempts,
                    )
                    time.sleep(sleep_for)
            raise ExternalServiceError(str(last_error) if last_error else "operation failed")

        return wrapper  # type: ignore[return-value]

    return decorator


def check_rate_limit(scope: str, key: str, limit: int, window_seconds: int) -> bool:
    """Simple in-process rate limiter with optional Redis backing."""
    if Settings.REDIS_URL:
        try:
            import redis

            client = redis.Redis.from_url(Settings.REDIS_URL, decode_responses=True)
            bucket = f"tbot:rl:{scope}:{key}:{int(time.time() // window_seconds)}"
            hits = int(client.incr(bucket))
            if hits == 1:
                client.expire(bucket, window_seconds)
            return hits <= limit
        except Exception:
            logger.debug("Redis rate limiter unavailable, falling back to in-memory")

    now = time.time()
    bucket_key = f"{scope}:{key}"
    with _RATE_LOCK:
        dq = _RATE_BUCKETS[bucket_key]
        while dq and now - dq[0] > window_seconds:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
    return True
