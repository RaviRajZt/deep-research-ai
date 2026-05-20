# ============================================
# Deep Research Platform - ResearchSession Repository
# ============================================
"""
Data access layer for ResearchSession entities.

WHY a concrete repository over direct session.execute():
- Encapsulates all query logic in one place
- Business logic in services stays clean
- Enables easy mocking in unit tests
- Consistent filtering, pagination, and ordering across callers
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ResearchStatus
from app.models.research_session import ResearchSession
from app.repositories.base import SQLAlchemyRepository


class ResearchSessionRepository(SQLAlchemyRepository[ResearchSession]):
    """
    Concrete repository for ResearchSession CRUD and domain queries.

    Inherits standard get_by_id / get_all / create / update / delete
    from SQLAlchemyRepository. Adds domain-specific query methods below.
    """

    model = ResearchSession

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ------------------------------------------------------------------
    # Domain Query Methods
    # ------------------------------------------------------------------

    async def get_by_status(
        self,
        status: ResearchStatus | str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ResearchSession]:
        """
        Return sessions filtered by status, newest first.
        Useful for polling PENDING sessions or listing COMPLETED history.
        """
        result = await self._session.execute(
            select(ResearchSession)
            .where(ResearchSession.status == str(status))
            .order_by(ResearchSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_active_sessions(self, limit: int = 50) -> list[ResearchSession]:
        """Return all non-terminal sessions (pending, planning, researching, etc.)."""
        terminal_states = [
            ResearchStatus.COMPLETED,
            ResearchStatus.FAILED,
            ResearchStatus.CANCELLED,
        ]
        result = await self._session.execute(
            select(ResearchSession)
            .where(ResearchSession.status.notin_([str(s) for s in terminal_states]))
            .order_by(ResearchSession.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        session_id: uuid.UUID,
        status: ResearchStatus | str,
        error_message: str | None = None,
    ) -> ResearchSession | None:
        """
        Transition a session to a new status.

        WHY a dedicated method:
        - Status transitions are the most common mutation
        - Centralizing it makes lifecycle logic auditable
        - Avoids scattered `setattr(session, 'status', ...)` calls
        """
        values: dict[str, Any] = {"status": str(status)}
        if error_message is not None:
            values["error_message"] = error_message

        await self._session.execute(
            update(ResearchSession)
            .where(ResearchSession.id == session_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        await self._session.flush()
        return await self.get_by_id(session_id)

    async def set_result(
        self,
        session_id: uuid.UUID,
        result_summary: str,
        result_token_count: int | None = None,
    ) -> ResearchSession | None:
        """
        Persist the final research result and mark session as COMPLETED.
        Called by the synthesizer agent when the pipeline completes.
        """
        values: dict[str, Any] = {
            "result_summary": result_summary,
            "status": ResearchStatus.COMPLETED,
        }
        if result_token_count is not None:
            values["result_token_count"] = result_token_count

        await self._session.execute(
            update(ResearchSession)
            .where(ResearchSession.id == session_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        await self._session.flush()
        return await self.get_by_id(session_id)

    async def count_by_status(self) -> dict[str, int]:
        """
        Return a dict of {status: count} across all sessions.
        Used by observability/analytics endpoints.
        """
        from sqlalchemy import func
        result = await self._session.execute(
            select(ResearchSession.status, func.count(ResearchSession.id))
            .group_by(ResearchSession.status)
        )
        return {row[0]: row[1] for row in result.all()}
