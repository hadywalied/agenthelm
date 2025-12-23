"""Tests for short-term memory backends."""

import asyncio
import pytest

from agenthelm.memory.short_term.in_memory import InMemoryShortTermMemory
from agenthelm.memory.short_term.sqlite import SqliteShortTermMemory


class TestInMemoryShortTermMemory:
    """Tests for InMemoryShortTermMemory."""

    @pytest.fixture
    def memory(self):
        """Create a fresh in-memory store."""
        return InMemoryShortTermMemory()

    @pytest.mark.asyncio
    async def test_set_and_get(self, memory):
        """Test basic set and get operations."""
        await memory.set("key1", "value1")
        result = await memory.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, memory):
        """Test getting a nonexistent key returns None."""
        result = await memory.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, memory):
        """Test deleting a key."""
        await memory.set("key1", "value1")
        await memory.delete("key1")
        result = await memory.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self, memory):
        """Test checking if key exists."""
        await memory.set("key1", "value1")
        assert await memory.exists("key1") is True
        assert await memory.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_keys_pattern(self, memory):
        """Test listing keys with pattern."""
        await memory.set("user:1:name", "Alice")
        await memory.set("user:2:name", "Bob")
        await memory.set("session:abc", "data")

        user_keys = await memory.keys("user:*")
        assert len(user_keys) == 2
        assert "user:1:name" in user_keys
        assert "user:2:name" in user_keys

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, memory):
        """Test that keys expire after TTL."""
        await memory.set("short_lived", "data", ttl=1)
        assert await memory.get("short_lived") == "data"

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await memory.get("short_lived") is None

    @pytest.mark.asyncio
    async def test_no_expiration_when_ttl_zero(self, memory):
        """Test that TTL=0 means no expiration."""
        await memory.set("permanent", "data", ttl=0)
        # Should still exist (no time-based check needed)
        assert await memory.get("permanent") == "data"

    @pytest.mark.asyncio
    async def test_complex_values(self, memory):
        """Test storing complex data structures."""
        data = {"name": "Alice", "scores": [1, 2, 3], "nested": {"a": 1}}
        await memory.set("complex", data)
        result = await memory.get("complex")
        assert result == data

    def test_clear(self, memory):
        """Test clearing all data."""
        asyncio.get_event_loop().run_until_complete(memory.set("key1", "v1"))
        asyncio.get_event_loop().run_until_complete(memory.set("key2", "v2"))
        memory.clear()
        result = asyncio.get_event_loop().run_until_complete(memory.get("key1"))
        assert result is None


class TestSqliteShortTermMemory:
    """Tests for SqliteShortTermMemory."""

    @pytest.fixture
    def memory(self, tmp_path):
        """Create a SQLite store in a temp directory."""
        db_path = tmp_path / "test.db"
        return SqliteShortTermMemory(db_path=db_path)

    @pytest.mark.asyncio
    async def test_set_and_get(self, memory):
        """Test basic set and get operations."""
        await memory.set("key1", "value1")
        result = await memory.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, memory):
        """Test getting a nonexistent key returns None."""
        result = await memory.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, memory):
        """Test deleting a key."""
        await memory.set("key1", "value1")
        await memory.delete("key1")
        result = await memory.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self, memory):
        """Test checking if key exists."""
        await memory.set("key1", "value1")
        assert await memory.exists("key1") is True
        assert await memory.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_keys_pattern(self, memory):
        """Test listing keys with pattern."""
        await memory.set("user:1:name", "Alice")
        await memory.set("user:2:name", "Bob")
        await memory.set("session:abc", "data")

        user_keys = await memory.keys("user:*")
        assert len(user_keys) == 2
        assert "user:1:name" in user_keys
        assert "user:2:name" in user_keys

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, memory):
        """Test that keys expire after TTL."""
        await memory.set("short_lived", "data", ttl=1)
        assert await memory.get("short_lived") == "data"

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await memory.get("short_lived") is None

    @pytest.mark.asyncio
    async def test_complex_values(self, memory):
        """Test storing complex data structures."""
        data = {"name": "Alice", "scores": [1, 2, 3], "nested": {"a": 1}}
        await memory.set("complex", data)
        result = await memory.get("complex")
        assert result == data

    @pytest.mark.asyncio
    async def test_persistence(self, tmp_path):
        """Test that data persists across instances."""
        db_path = tmp_path / "persist.db"

        mem1 = SqliteShortTermMemory(db_path=db_path)
        await mem1.set("key", "value")

        mem2 = SqliteShortTermMemory(db_path=db_path)
        result = await mem2.get("key")
        assert result == "value"

    def test_clear(self, memory):
        """Test clearing all data."""
        asyncio.get_event_loop().run_until_complete(memory.set("key1", "v1"))
        memory.clear()
        result = asyncio.get_event_loop().run_until_complete(memory.get("key1"))
        assert result is None
