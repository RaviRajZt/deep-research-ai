from __future__ import annotations

import structlog
from uuid import UUID
from app.redis_.cache import CacheService

logger = structlog.get_logger(__name__)


class ChunkStorageService:
    """Manages temporary storage of raw text chunks in Redis to keep LangGraph state lightweight.

    Uses CacheService with a dedicated 'chunks' namespace.
    """

    def __init__(self) -> None:
        # Initialize CacheService with 'chunks' namespace
        self._cache = CacheService(namespace="chunks")

    def _build_key(self, session_id: UUID, source_id: UUID) -> str:
        """Construct the Redis key for source chunks."""
        return f"{session_id}:{source_id}"

    async def store_chunks(
        self, session_id: UUID, source_id: UUID, chunks: list[str], ttl: int = 86400
    ) -> bool:
        """Store a list of raw text chunks in Redis with a TTL (default 24 hours)."""
        if not chunks:
            return True

        key = self._build_key(session_id, source_id)
        logger.info(
            "Storing text chunks in Redis",
            session_id=str(session_id),
            source_id=str(source_id),
            chunks_count=len(chunks),
        )
        return await self._cache.set(key, chunks, ttl=ttl)

    async def get_chunks(self, session_id: UUID, source_id: UUID) -> list[str] | None:
        """Retrieve the list of raw text chunks from Redis.

        Returns None if expired or missing.
        """
        key = self._build_key(session_id, source_id)
        chunks = await self._cache.get(key)
        if chunks is None:
            logger.debug(
                "Chunk cache miss",
                session_id=str(session_id),
                source_id=str(source_id),
            )
            return None

        logger.debug(
            "Chunk cache hit",
            session_id=str(session_id),
            source_id=str(source_id),
            chunks_count=len(chunks),
        )
        return list(chunks)

    async def delete_chunks(self, session_id: UUID, source_id: UUID) -> bool:
        """Remove source chunks from Redis cache once processing is complete."""
        key = self._build_key(session_id, source_id)
        logger.info(
            "Deleting text chunks from Redis",
            session_id=str(session_id),
            source_id=str(source_id),
        )
        return await self._cache.delete(key)
