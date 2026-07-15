"""Token bucket rate limiter for Google API calls.

Enforces per-API rate limits to prevent 429 errors proactively.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from google_forms_mcp.infrastructure.logging import get_logger

logger = get_logger("rate_limiter")


@dataclass
class BucketConfig:
    """Configuration for a single rate limit bucket."""

    max_tokens: float
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = self.max_tokens
        self.last_refill = time.monotonic()


class RateLimiter:
    """Thread-safe token bucket rate limiter.

    Supports multiple named buckets, each with its own rate limit.
    When a bucket is exhausted, acquire() blocks until tokens are available.

    Example:
        limiter = RateLimiter()
        limiter.configure("forms_read", max_per_minute=390)
        limiter.acquire("forms_read")  # blocks if rate limit would be exceeded
    """

    def __init__(self) -> None:
        self._buckets: dict[str, BucketConfig] = {}
        self._lock = threading.Lock()

    def configure(self, name: str, max_per_minute: float) -> None:
        """Configure a rate limit bucket.

        Args:
            name: Bucket name (e.g., 'forms_read', 'drive_write').
            max_per_minute: Maximum requests per minute.
        """
        with self._lock:
            self._buckets[name] = BucketConfig(
                max_tokens=max_per_minute,
                refill_rate=max_per_minute / 60.0,
            )

    def acquire(self, name: str, tokens: float = 1.0) -> None:
        """Acquire tokens from a bucket, blocking if necessary.

        Args:
            name: Bucket name.
            tokens: Number of tokens to consume (default 1).
        """
        if name not in self._buckets:
            return  # No limit configured for this bucket

        while True:
            with self._lock:
                bucket = self._buckets[name]
                self._refill(bucket)

                if bucket.tokens >= tokens:
                    bucket.tokens -= tokens
                    return

                # Calculate wait time for enough tokens
                deficit = tokens - bucket.tokens
                wait_time = deficit / bucket.refill_rate

            logger.debug(
                "Rate limit: waiting %.2fs for bucket '%s' (%.1f tokens needed)",
                wait_time,
                name,
                deficit,
            )
            time.sleep(min(wait_time, 1.0))  # Check every second at most

    def _refill(self, bucket: BucketConfig) -> None:
        """Refill tokens based on elapsed time. Must be called with lock held."""
        now = time.monotonic()
        elapsed = now - bucket.last_refill
        bucket.tokens = min(
            bucket.max_tokens,
            bucket.tokens + elapsed * bucket.refill_rate,
        )
        bucket.last_refill = now


def create_default_rate_limiter() -> RateLimiter:
    """Create a rate limiter pre-configured with Google API limits.

    Configures conservative limits (80% of actual quota) to leave headroom.
    """
    limiter = RateLimiter()

    # Google Forms API — 390 reads/min/user, using 80% = 312
    limiter.configure("forms_read", max_per_minute=312)
    # Google Forms API — expensive reads (responses.list) — 180/min/user, 80% = 144
    limiter.configure("forms_read_expensive", max_per_minute=144)
    # Google Forms API — writes, same quota as reads
    limiter.configure("forms_write", max_per_minute=312)

    # Google Drive API — 12,000 reads/min/project, per-user ~1,000
    limiter.configure("drive_read", max_per_minute=800)
    # Google Drive API — 1,200 writes/min/project, per-user ~100
    limiter.configure("drive_write", max_per_minute=80)

    # Google Sheets API — 300 reads/min/user, 80% = 240
    limiter.configure("sheets_read", max_per_minute=240)
    # Google Sheets API — 60 writes/min/user, 80% = 48
    limiter.configure("sheets_write", max_per_minute=48)

    return limiter
