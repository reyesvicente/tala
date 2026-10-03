"""In-memory sliding-window rate limiting.

Fine because Tala runs as a single instance (the Whisper job queue already requires that).
Counts reset on restart, which is acceptable for abuse protection.
"""

import math
import threading
import time
from collections import deque

MAX_KEYS = 10_000


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> deque[float]:
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        return hits

    def retry_after(self, key: str) -> int:
        """Seconds until `key` may try again; 0 if it's allowed now. Doesn't record a hit."""
        now = time.monotonic()
        with self._lock:
            hits = self._recent(key, now)
            if len(hits) < self.limit:
                return 0
            return max(1, math.ceil(hits[0] + self.window - now))

    def hit(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > MAX_KEYS:
                self._prune(now)
            self._recent(key, now).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()

    def _prune(self, now: float) -> None:
        for key in list(self._hits):
            if not self._recent(key, now):
                del self._hits[key]


login_by_ip = RateLimiter(limit=20, window_seconds=5 * 60)
login_failures_by_email = RateLimiter(limit=5, window_seconds=15 * 60)
register_by_ip = RateLimiter(limit=5, window_seconds=60 * 60)
forgot_by_ip = RateLimiter(limit=5, window_seconds=15 * 60)
reset_by_ip = RateLimiter(limit=10, window_seconds=15 * 60)

ALL = [login_by_ip, login_failures_by_email, register_by_ip, forgot_by_ip, reset_by_ip]
