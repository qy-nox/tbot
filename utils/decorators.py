"""Common decorators."""

from __future__ import annotations

from functools import wraps
from time import perf_counter


def timed(fn):
    """Measure function execution time and store last value on wrapper.

    The most recent elapsed seconds can be accessed via ``wrapped.last_elapsed``.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = fn(*args, **kwargs)
        wrapper.last_elapsed = perf_counter() - start
        return result

    wrapper.last_elapsed = 0.0
    return wrapper
