"""Base classes for AgentHelm memory backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    """Result from semantic memory search."""

    id: str
    text: str
    score: float
    metadata: dict[str, Any] | None = None


class BaseShortTermMemory(ABC):
    """Abstract base class for short-term (key-value) memory."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if not found or expired."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set a value with optional TTL in seconds."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        ...

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple keys. Default implementation calls get() for each."""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def close(self) -> None:
        """Close any connections. Override if needed."""
        pass


class BaseSemanticMemory(ABC):
    """Abstract base class for semantic (vector) memory."""

    @abstractmethod
    async def store(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> str:
        """Store text with optional metadata. Returns the ID."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar texts. Returns ranked results."""
        ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Delete entries by ID."""
        ...

    async def store_many(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        """Store multiple texts. Default implementation calls store() for each."""
        ids = []
        for i, text in enumerate(texts):
            meta = metadatas[i] if metadatas else None
            id = await self.store(text, meta)
            ids.append(id)
        return ids

    async def close(self) -> None:
        """Close any connections. Override if needed."""
        pass
