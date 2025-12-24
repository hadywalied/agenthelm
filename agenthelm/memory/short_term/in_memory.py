"""In-memory short-term memory backend with lazy TTL expiration."""

import time
from typing import Any

from agenthelm.memory.base import BaseShortTermMemory


class InMemoryShortTermMemory(BaseShortTermMemory):
    """
    In-memory key-value store with TTL support.

    Uses lazy expiration: expired entries are removed on access.
    No external dependencies required.

    Example:
        memory = InMemoryShortTermMemory()
        await memory.set("user:123:name", "Alice", ttl=3600)
        name = await memory.get("user:123:name")
    """

    def __init__(self):
        # Storage: {key: (value, expiry_timestamp)}
        # expiry_timestamp is None for no expiration
        self._store: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if not found or expired."""
        if key not in self._store:
            return None

        value, expiry = self._store[key]

        # Check if expired
        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return None

        return value

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set a value with TTL in seconds.

        Args:
            key: The key to store under
            value: Any JSON-serializable value
            ttl: Time-to-live in seconds (default: 1 hour, 0 for no expiration)
        """
        if ttl > 0:
            expiry = time.time() + ttl
        else:
            expiry = None

        self._store[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        """Delete a key if it exists."""
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        if key not in self._store:
            return False

        _, expiry = self._store[key]

        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return False

        return True

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple keys efficiently."""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def keys(self, pattern: str = "*") -> list[str]:
        """
        List keys matching a pattern.

        Supports simple wildcards:
        - '*' matches everything
        - 'prefix:*' matches keys starting with 'prefix:'
        - '*:suffix' matches keys ending with ':suffix'
        """
        import fnmatch

        # Clean up expired keys first
        now = time.time()
        expired = [
            k for k, (_, exp) in self._store.items() if exp is not None and now > exp
        ]
        for key in expired:
            del self._store[key]

        # Match pattern
        return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]

    def clear(self) -> None:
        """Clear all stored data."""
        self._store.clear()

    def __len__(self) -> int:
        """Return number of stored items (including expired ones)."""
        return len(self._store)
