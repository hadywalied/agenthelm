"""MemoryHub - Unified interface to short-term and semantic memory."""

from pathlib import Path

from agenthelm.memory.base import BaseShortTermMemory, BaseSemanticMemory
from agenthelm.memory.short_term.in_memory import InMemoryShortTermMemory
from agenthelm.memory.semantic import SemanticMemory


class MemoryHub:
    """
    Unified interface to AgentHelm memory backends.

    Provides access to both short-term (key-value) and semantic (vector) memory
    with automatic backend selection based on configuration.

    Examples:
        # In-memory (default) - zero config, ephemeral
        hub = MemoryHub()

        # Local persistence - no Docker needed
        hub = MemoryHub(data_dir="./data")

        # Network mode - for production scaling
        hub = MemoryHub(redis_url="redis://...", qdrant_url="http://...")
    """

    def __init__(
        self,
        # Mode selection
        data_dir: str | Path | None = None,
        # Network backends (optional)
        redis_url: str | None = None,
        qdrant_url: str | None = None,
        # Advanced options
        collection_name: str | None = None,
        embedding_model: str | None = None,
    ):
        """
        Initialize MemoryHub.

        Args:
            data_dir: Directory for local persistence. If provided, uses local mode.
            redis_url: Redis server URL. If provided, uses Redis for short-term.
            qdrant_url: Qdrant server URL. If provided, uses network Qdrant.
            collection_name: Custom Qdrant collection name.
            embedding_model: Custom embedding model for semantic memory.
        """
        self._short_term: BaseShortTermMemory | None = None
        self._semantic: BaseSemanticMemory | None = None

        # Determine modes based on configuration
        self._data_dir = Path(data_dir) if data_dir else None
        self._redis_url = redis_url
        self._qdrant_url = qdrant_url
        self._collection_name = collection_name
        self._embedding_model = embedding_model

    @property
    def short_term(self) -> BaseShortTermMemory:
        """Get short-term memory backend (lazy initialization)."""
        if self._short_term is None:
            self._short_term = self._create_short_term()
        return self._short_term

    @property
    def semantic(self) -> BaseSemanticMemory:
        """Get semantic memory backend (lazy initialization)."""
        if self._semantic is None:
            self._semantic = self._create_semantic()
        return self._semantic

    def _create_short_term(self) -> BaseShortTermMemory:
        """Create short-term memory backend based on configuration."""
        if self._redis_url:
            # Network mode: use Redis
            from agenthelm.memory.short_term.redis import RedisShortTermMemory

            return RedisShortTermMemory(url=self._redis_url)
        elif self._data_dir:
            # Local mode: use SQLite
            from agenthelm.memory.short_term.sqlite import SqliteShortTermMemory

            db_path = self._data_dir / "short_term.db"
            self._data_dir.mkdir(parents=True, exist_ok=True)
            return SqliteShortTermMemory(db_path=str(db_path))
        else:
            # In-memory mode (default)
            return InMemoryShortTermMemory()

    def _create_semantic(self) -> BaseSemanticMemory:
        """Create semantic memory backend based on configuration."""
        if self._qdrant_url:
            # Network mode
            return SemanticMemory(
                mode="network",
                url=self._qdrant_url,
                collection_name=self._collection_name,
                embedding_model=self._embedding_model,
            )
        elif self._data_dir:
            # Local mode
            qdrant_path = self._data_dir / "qdrant"
            self._data_dir.mkdir(parents=True, exist_ok=True)
            return SemanticMemory(
                mode="local",
                path=str(qdrant_path),
                collection_name=self._collection_name,
                embedding_model=self._embedding_model,
            )
        else:
            # In-memory mode (default)
            return SemanticMemory(
                mode="memory",
                collection_name=self._collection_name,
                embedding_model=self._embedding_model,
            )

    async def close(self) -> None:
        """Close all backends and release resources."""
        if self._short_term:
            await self._short_term.close()
        if self._semantic:
            await self._semantic.close()

    async def __aenter__(self) -> "MemoryHub":
        """Async context manager support."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager cleanup."""
        await self.close()
