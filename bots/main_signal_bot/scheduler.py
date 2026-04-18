"""Advanced scheduling helper for periodic scan tasks."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

ScheduledTask = Callable[[], Awaitable[None]]
logger = logging.getLogger(__name__)


class AsyncScheduler:
    """Small async scheduler with graceful cancellation support."""

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task[None]] = []

    def every(self, seconds: float, task: ScheduledTask) -> None:
        """Schedule *task* to run repeatedly."""

        async def runner() -> None:
            while True:
                await task()
                await asyncio.sleep(seconds)

        self._tasks.append(asyncio.create_task(runner()))

    async def stop(self) -> None:
        """Cancel all scheduled tasks."""
        for task in self._tasks:
            task.cancel()
        results = await asyncio.gather(*self._tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                logger.warning("Scheduler task exited with exception: %s", result)
        self._tasks.clear()
