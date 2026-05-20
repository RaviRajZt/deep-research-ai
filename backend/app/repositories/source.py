# ============================================
# Deep Research Platform - Source Repository
# ============================================
"""
Data access layer for Source entities.

Sources are fetched in parallel by the search agent,
then updated as content is processed through the pipeline.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.repositories.base import SQLAlchemyRepository


class SourceRepository(SQLAlchemyRepository[Source]):
    """
    Concrete repository for Source CRUD and fetch-pipeline queries.
    """

    model = Source

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ------------------------------------------------------------------
    # Domain Query Methods
    # ------------------------------------------------------------------

    async def get_by_session(
        self,
        session_id: uuid.UUID,
        fetch_status: str | None = None,
    ) -> list[Source]:
        """
        Return all sources for a session, optionally filtered by fetch_status.

        Args:
            session_id: Parent research session ID.
            fetch_status: If provided, filter to sources with this status.
        """
        query = select(Source).where(Source.session_id == session_id)
        if fetch_status is not None:
            query = query.where(Source.fetch_status == fetch_status)
        query = query.order_by(Source.created_at.asc())

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_content_hash(self, content_hash: str) -> Source | None:
        """
        Find an existing source by its content hash.
        Enables cross-session deduplication — if the same page was
        already fetched in a previous session, reuse its summary.
        """
        result = await self._session.execute(
            select(Source).where(Source.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def bulk_create(self, sources: list[dict[str, Any]]) -> list[Source]:
        """
        Insert multiple sources in a single flush.
        Used by the search agent when it discovers a batch of URLs.

        WHY bulk_create over N create() calls:
        - Avoids N round trips to the DB
        - Single flush = single transaction checkpoint
        """
        instances = [Source(**s) for s in sources]
        self._session.add_all(instances)
        await self._session.flush()
        for instance in instances:
            await self._session.refresh(instance)
        return instances

    async def update_fetch_status(
        self,
        source_id: uuid.UUID,
        fetch_status: str,
        fetch_error: str | None = None,
        content_hash: str | None = None,
        raw_token_count: int | None = None,
        chunk_count: int | None = None,
        title: str | None = None,
        source_metadata: dict[str, Any] | None = None,
    ) -> Source | None:
        """
        Update a source after a fetch attempt (success or failure).
        Called by the extractor pipeline as each URL is processed.
        """
        values: dict[str, Any] = {"fetch_status": fetch_status}
        if fetch_error is not None:
            values["fetch_error"] = fetch_error
        if content_hash is not None:
            values["content_hash"] = content_hash
        if raw_token_count is not None:
            values["raw_token_count"] = raw_token_count
        if chunk_count is not None:
            values["chunk_count"] = chunk_count
        if title is not None:
            values["title"] = title
        if source_metadata is not None:
            values["source_metadata"] = source_metadata

        await self._session.execute(
            update(Source)
            .where(Source.id == source_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        await self._session.flush()
        return await self.get_by_id(source_id)

    async def get_fetched_count(self, session_id: uuid.UUID) -> int:
        """Return count of successfully fetched sources for a session."""
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count(Source.id))
            .where(Source.session_id == session_id)
            .where(Source.fetch_status == "fetched")
        )
        return result.scalar_one()
