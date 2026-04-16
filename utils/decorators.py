"""Common decorators."""

from __future__ import annotations

from functools import wraps
from time import perf_counter


def timed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        result = fn(*args, **kwargs)
        _ = perf_counter() - start
        return result

    return wrapper
