# services/queue_manager.py
"""
Asyncio-based request queue with concurrency limiting.

Prevents overloading the LangGraph pipeline by limiting
the number of concurrent requests processed simultaneously.

Each uvicorn worker has its own independent RequestQueueManager instance.
With --workers 3 and max_concurrent=5, effective concurrency = 15.
"""
import asyncio
from contextlib import asynccontextmanager
from config import settings
import logging

logger = logging.getLogger(__name__)


class QueueFullError(Exception):
    """Raised when the request queue is full and cannot accept new requests."""
    pass


class RequestQueueManager:
    """
    Asyncio-based concurrency limiter for the LangGraph pipeline.

    - max_concurrent: Maximum number of requests processed simultaneously
    - max_waiting: Maximum number of requests waiting in queue
    - When max_waiting is exceeded, new requests are rejected with QueueFullError
    """

    def __init__(self, max_concurrent: int = 5, max_waiting: int = 20):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._waiting_count = 0
        self._max_waiting = max_waiting
        self._max_concurrent = max_concurrent
        logger.info(
            f"[RequestQueue] Initialized: max_concurrent={max_concurrent}, "
            f"max_waiting={max_waiting}"
        )

    async def acquire(self) -> bool:
        """
        Acquire a processing slot. Waits if all slots are busy.
        Returns False (reject) if waiting queue is full.
        """
        if self._waiting_count >= self._max_waiting:
            logger.warning(
                f"[RequestQueue] Queue full: {self._waiting_count} waiting, "
                f"rejecting new request"
            )
            return False

        self._waiting_count += 1
        try:
            await self._semaphore.acquire()
        finally:
            self._waiting_count -= 1
        return True

    def release(self):
        """Release a processing slot."""
        self._semaphore.release()

    @asynccontextmanager
    async def throttle(self):
        """
        Async context manager for throttling requests.

        Usage:
            async with request_queue.throttle():
                # process request
                result = await pipeline.run(...)

        Raises:
            QueueFullError: If the waiting queue is full
        """
        acquired = await self.acquire()
        if not acquired:
            raise QueueFullError("Server is busy. Please try again later.")
        try:
            yield
        finally:
            self.release()

    @property
    def stats(self) -> dict:
        """Return current queue statistics."""
        return {
            "max_concurrent": self._max_concurrent,
            "max_waiting": self._max_waiting,
            "waiting_count": self._waiting_count,
            "available_slots": self._semaphore._value,
        }


# Module-level singleton instance
request_queue = RequestQueueManager(
    max_concurrent=settings.MAX_CONCURRENT_REQUESTS,
    max_waiting=settings.MAX_WAITING_REQUESTS,
)
