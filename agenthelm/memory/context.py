"""Session-scoped MemoryContext for managing memory lifecycle."""

import uuid
from typing import Any

from agenthelm.memory.hub import MemoryHub


class MemoryContext:
    """
    Session-scoped context manager for memory operations.

    Provides a scoped namespace within the MemoryHub for a single session,
    preventing key collisions between concurrent sessions and enabling
    easy cleanup of session-specific data.

    Examples:
        # Using with async context manager
        async with MemoryContext(hub, session_id="user-123") as ctx:
            await ctx.set("last_query", "What is AI?")
            await ctx.store_memory("User asked about AI basics.")

        # Manual lifecycle management
        ctx = MemoryContext(hub)
        await ctx.set("key", "value")
        await ctx.cleanup()  # Clean up session data
    """

    def __init__(
        self,
        hub: MemoryHub,
        session_id: str | None = None,
        cleanup_on_exit: bool = True,
    ):
        """
        Initialize MemoryContext.

        Args:
            hub: The MemoryHub instance to use
            session_id: Optional session identifier (auto-generated if not provided)
            cleanup_on_exit: Whether to clean up session data on exit
        """
        self.hub = hub
        self.session_id = session_id or str(uuid.uuid4())
        self.cleanup_on_exit = cleanup_on_exit
        self._stored_memory_ids: list[str] = []

    def _scoped_key(self, key: str) -> str:
        """Create a session-scoped key."""
        return f"session:{self.session_id}:{key}"

    # Short-term memory operations (scoped by session)

    async def get(self, key: str) -> Any | None:
        """Get a session-scoped value."""
        return await self.hub.short_term.get(self._scoped_key(key))

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set a session-scoped value with TTL."""
        await self.hub.short_term.set(self._scoped_key(key), value, ttl)

    async def delete(self, key: str) -> None:
        """Delete a session-scoped key."""
        await self.hub.short_term.delete(self._scoped_key(key))

    # Semantic memory operations (tagged with session)

    async def store_memory(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Store a memory with session metadata.

        Args:
            text: The text to store
            metadata: Additional metadata

        Returns:
            The ID of the stored memory
        """
        full_metadata = {"session_id": self.session_id}
        if metadata:
            full_metadata.update(metadata)

        memory_id = await self.hub.semantic.store(text, metadata=full_metadata)
        self._stored_memory_ids.append(memory_id)
        return memory_id

    async def recall(
        self,
        query: str,
        top_k: int = 5,
        session_only: bool = False,
    ) -> list:
        """
        Search semantic memory.

        Args:
            query: Search query
            top_k: Number of results to return
            session_only: If True, only search within this session's memories

        Returns:
            List of SearchResult objects
        """
        filter_dict = None
        if session_only:
            filter_dict = {"session_id": self.session_id}

        return await self.hub.semantic.search(query, top_k=top_k, filter=filter_dict)

    # Lifecycle management

    async def cleanup(self) -> None:
        """Clean up all session-scoped short-term memory keys."""
        pattern = f"session:{self.session_id}:*"
        keys = await self.hub.short_term.keys(pattern)
        for key in keys:
            await self.hub.short_term.delete(key)

    async def cleanup_semantic(self) -> None:
        """Clean up semantic memories stored in this session."""
        if self._stored_memory_ids:
            await self.hub.semantic.delete(self._stored_memory_ids)
            self._stored_memory_ids.clear()

    async def __aenter__(self) -> "MemoryContext":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with optional cleanup."""
        if self.cleanup_on_exit:
            await self.cleanup()
