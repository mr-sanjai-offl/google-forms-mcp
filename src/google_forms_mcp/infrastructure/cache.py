"""In-memory LRU cache with TTL for reducing Google API calls.

Caches form metadata and other read-heavy data to minimize redundant API calls.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any


class TTLCache:
    """Thread-safe in-memory LRU cache with per-entry TTL.

    Example:
        cache = TTLCache(max_size=100, default_ttl=300)
        cache.set("form:abc123", form_data)
        result = cache.get("form:abc123")  # Returns form_data if not expired
    """

    def __init__(self, max_size: int = 256, default_ttl: float = 300.0) -> None:
        """Initialize the cache.

        Args:
            max_size: Maximum number of entries before LRU eviction.
            default_ttl: Default time-to-live in seconds.
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Get a value from the cache.

        Returns None if the key is missing or expired.

        Args:
            key: Cache key.

        Returns:
            Cached value or None.
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]
            if time.monotonic() > expiry:
                # Entry expired — remove it
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds. Uses default_ttl if not specified.
        """
        effective_ttl = ttl if ttl is not None else self._default_ttl
        expiry = time.monotonic() + effective_ttl

        with self._lock:
            if key in self._cache:
                # Update existing entry
                self._cache.move_to_end(key)
                self._cache[key] = (value, expiry)
            else:
                # Add new entry
                if len(self._cache) >= self._max_size:
                    # Evict least recently used
                    self._cache.popitem(last=False)
                self._cache[key] = (value, expiry)

    def invalidate(self, key: str) -> None:
        """Remove a specific entry from the cache.

        Args:
            key: Cache key to invalidate.
        """
        with self._lock:
            self._cache.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all entries matching a key prefix.

        Useful for invalidating all cached data for a specific form.

        Args:
            prefix: Key prefix to match (e.g., "form:abc123").
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache[key]

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        """Return the current number of entries in the cache."""
        with self._lock:
            return len(self._cache)
