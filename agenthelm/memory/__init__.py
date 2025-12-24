"""
AgentHelm Memory Hub - Pluggable memory system with zero-Docker defaults.

Example usage:
    from agenthelm.memory import MemoryHub, MemoryContext

    # In-memory (default, ephemeral)
    hub = MemoryHub()

    # Local file persistence
    hub = MemoryHub(data_dir="./data")

    # Session-scoped context
    async with MemoryContext(hub, session_id="user-123") as ctx:
        await ctx.set("last_query", "What is AI?")
        await ctx.store_memory("User asked about AI basics.")
"""

from agenthelm.memory.base import (
    BaseShortTermMemory,
    BaseSemanticMemory,
    SearchResult,
)
from agenthelm.memory.hub import MemoryHub
from agenthelm.memory.context import MemoryContext
from agenthelm.memory.semantic import SemanticMemory
from agenthelm.memory.short_term import (
    InMemoryShortTermMemory,
    SqliteShortTermMemory,
)

__all__ = [
    # Abstract bases
    "BaseShortTermMemory",
    "BaseSemanticMemory",
    "SearchResult",
    # High-level interfaces
    "MemoryHub",
    "MemoryContext",
    # Concrete implementations
    "SemanticMemory",
    "InMemoryShortTermMemory",
    "SqliteShortTermMemory",
]
