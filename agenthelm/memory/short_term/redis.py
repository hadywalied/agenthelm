"""Redis-based short-term memory for network/production deployments."""

import json
from typing import Any

from agenthelm.memory.base import BaseShortTermMemory


class RedisShortTermMemory(BaseShortTermMemory):
    """
    Redis-based key-value store with TTL support.

    Provides scalable network storage for production deployments.
    Requires a running Redis server (Docker or managed service).

    Example:
        memory = RedisShortTermMemory(url="redis://localhost:6379")
        await memory.set("user:123:name", "Alice", ttl=3600)
        name = await memory.get("user:123:name")
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "agenthelm:",
    ):
        """
        Initialize Redis short-term memory.

        Args:
            url: Redis connection URL
            prefix: Key prefix for namespacing
        """
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError(
                "redis package is required for RedisShortTermMemory. "
                "Install with: pip install redis"
            )

        self.prefix = prefix
        self._redis = redis.from_url(url, decode_responses=True)

    def _prefixed_key(self, key: str) -> str:
        """Add prefix to key for namespacing."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if not found or expired."""
        value_json = await self._redis.get(self._prefixed_key(key))
        if value_json is None:
            return None
        return json.loads(value_json)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set a value with TTL in seconds.

        Args:
            key: The key to store under
            value: Any JSON-serializable value
            ttl: Time-to-live in seconds (default: 1 hour, 0 for no expiration)
        """
        value_json = json.dumps(value)
        prefixed = self._prefixed_key(key)

        if ttl > 0:
            await self._redis.setex(prefixed, ttl, value_json)
        else:
            await self._redis.set(prefixed, value_json)

    async def delete(self, key: str) -> None:
        """Delete a key if it exists."""
        await self._redis.delete(self._prefixed_key(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return await self._redis.exists(self._prefixed_key(key)) > 0

    async def keys(self, pattern: str = "*") -> list[str]:
        """
        List keys matching a pattern.

        Uses Redis SCAN for memory-efficient iteration.
        Pattern uses Redis glob-style matching (*, ?, []).
        """
        full_pattern = self._prefixed_key(pattern)
        matched_keys = []

        # Use SCAN for efficiency with large key sets
        cursor = 0
        while True:
            cursor, keys = await self._redis.scan(cursor=cursor, match=full_pattern)
            # Remove prefix from returned keys
            for key in keys:
                if key.startswith(self.prefix):
                    matched_keys.append(key[len(self.prefix) :])
            if cursor == 0:
                break

        return matched_keys

    def clear(self) -> None:
        """
        Clear all stored data with this prefix.

        Note: This is a blocking operation for simplicity.
        For async clearing, use an async context.
        """
        import asyncio

        async def _clear():
            keys = await self.keys("*")
            if keys:
                prefixed_keys = [self._prefixed_key(k) for k in keys]
                await self._redis.delete(*prefixed_keys)

        asyncio.get_event_loop().run_until_complete(_clear())

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.close()
