"""Semantic memory backend using Qdrant with three modes: memory, local, network."""

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from agenthelm.memory.base import BaseSemanticMemory, SearchResult


class SemanticMemory(BaseSemanticMemory):
    """
    Semantic memory using Qdrant vector database.

    Supports three modes:
    - "memory": In-memory, ephemeral (no persistence)
    - "local": Local file storage (persistent, no Docker)
    - "network": Remote Qdrant server (production scaling)

    Uses Qdrant's FastEmbed for automatic embedding generation.

    Example:
        # In-memory (default)
        memory = SemanticMemory()

        # Local file persistence
        memory = SemanticMemory(mode="local", path="./data/qdrant")

        # Network (Docker/Cloud)
        memory = SemanticMemory(mode="network", url="http://localhost:6333")
    """

    DEFAULT_COLLECTION = "agenthelm_memory"
    DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(
        self,
        mode: str = "memory",
        path: str | None = None,
        url: str | None = None,
        collection_name: str | None = None,
        embedding_model: str | None = None,
    ):
        """
        Initialize SemanticMemory.

        Args:
            mode: "memory", "local", or "network"
            path: Directory for local mode storage
            url: Qdrant server URL for network mode
            collection_name: Name of the Qdrant collection
            embedding_model: FastEmbed model name
        """
        self.mode = mode
        self.collection_name = collection_name or self.DEFAULT_COLLECTION
        self.embedding_model = embedding_model or self.DEFAULT_EMBEDDING_MODEL

        # Initialize Qdrant client based on mode
        if mode == "memory":
            self.client = QdrantClient(":memory:")
        elif mode == "local":
            if path is None:
                path = "./qdrant_data"
            self.client = QdrantClient(path=path)
        elif mode == "network":
            if url is None:
                url = "http://localhost:6333"
            self.client = QdrantClient(url=url)
        else:
            raise ValueError(
                f"Unknown mode: {mode}. Use 'memory', 'local', or 'network'."
            )

        # Track if collection is initialized
        self._collection_initialized = False

    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        if self._collection_initialized:
            return

        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            # Get embedding dimension from the model
            # all-MiniLM-L6-v2 produces 384-dimensional embeddings
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        self._collection_initialized = True

    def _embed_text(self, text: str) -> list[float]:
        """Generate embedding for text using FastEmbed."""
        # Use Qdrant's built-in embedding via the client
        # This requires qdrant-client[fastembed]
        from fastembed import TextEmbedding

        if not hasattr(self, "_embedding_model"):
            self._embedding_model = TextEmbedding(model_name=self.embedding_model)

        embeddings = list(self._embedding_model.embed([text]))
        return embeddings[0].tolist()

    async def store(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        id: str | None = None,
    ) -> str:
        """Store text with optional metadata. Returns the ID."""
        self._ensure_collection()

        if id is None:
            id = str(uuid.uuid4())

        embedding = self._embed_text(text)

        payload = {"text": text}
        if metadata:
            payload.update(metadata)

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        return id

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for similar texts. Returns ranked results."""
        self._ensure_collection()

        query_embedding = self._embed_text(query)

        # Build filter if provided
        qdrant_filter = None
        if filter:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=qdrant_filter,
            limit=top_k,
        )

        return [
            SearchResult(
                id=str(hit.id),
                text=hit.payload.get("text", ""),
                score=hit.score,
                metadata={k: v for k, v in hit.payload.items() if k != "text"},
            )
            for hit in results
        ]

    async def delete(self, ids: list[str]) -> None:
        """Delete entries by ID."""
        self._ensure_collection()

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids,
        )

    async def store_many(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        """Store multiple texts efficiently."""
        self._ensure_collection()

        points = []
        ids = []

        for i, text in enumerate(texts):
            id = str(uuid.uuid4())
            ids.append(id)

            embedding = self._embed_text(text)

            payload = {"text": text}
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])

            points.append(
                PointStruct(
                    id=id,
                    vector=embedding,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return ids

    async def close(self) -> None:
        """Close the Qdrant client."""
        self.client.close()

    def clear(self) -> None:
        """Delete all entries in the collection."""
        if self._collection_initialized:
            self.client.delete_collection(self.collection_name)
            self._collection_initialized = False
