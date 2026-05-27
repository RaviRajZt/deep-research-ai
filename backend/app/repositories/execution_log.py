# ============================================
# Deep Research Platform - ExecutionLog Repository
# ============================================
"""
Data access layer for ExecutionLog entities.

ExecutionLogs are write-heavy and read-often:
- Written by agents on every step transition
- Read by SSE streaming to push progress to frontend
- Read by analytics for per-session timelines
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_log import ExecutionLog
from app.repositories.base import SQLAlchemyRepository


class ExecutionLogRepository(SQLAlchemyRepository[ExecutionLog]):
    """
    Concrete repository for ExecutionLog CRUD and timeline queries.

    Inherits standard CRUD from SQLAlchemyRepository.
    Adds step-specific append and query methods.
    """

    model = ExecutionLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ------------------------------------------------------------------
    # Domain Query Methods
    # ------------------------------------------------------------------

    async def get_by_session(
        self,
        session_id: uuid.UUID,
        limit: int = 200,
    ) -> list[ExecutionLog]:
        """
        Return all execution steps for a session, ordered by step_order then created_at.
        This is the primary query for the agent timeline UI.
        """
        result = await self._session.execute(
            select(ExecutionLog)
            .where(ExecutionLog.session_id == session_id)
            .order_by(
                ExecutionLog.step_order.asc().nullsfirst(),
                ExecutionLog.created_at.asc(),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_by_session(
        self,
        session_id: uuid.UUID,
        limit: int = 10,
    ) -> list[ExecutionLog]:
        """
        Return the N most recent steps for a session.
        Used by SSE to resume streaming from last known position.
        """
        result = await self._session.execute(
            select(ExecutionLog)
            .where(ExecutionLog.session_id == session_id)
            .order_by(ExecutionLog.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def append_step(
        self,
        session_id: uuid.UUID,
        agent_role: str,
        step_name: str,
        status: str = "running",
        message: str | None = None,
        step_order: int | None = None,
        step_metadata: dict[str, Any] | None = None,
    ) -> ExecutionLog:
        """
        Append a new execution step log entry.

        WHY a dedicated method instead of create(**kwargs):
        - Enforces required fields at the callsite
        - Provides clear intent: this is an append, not a generic create
        - Avoids accidental omission of session_id in agent code
        """
        log = await self.create(
            session_id=session_id,
            agent_role=agent_role,
            step_name=step_name,
            status=status,
            message=message,
            step_order=step_order,
            step_metadata=step_metadata,
        )
        try:
            from app.services.stream import StreamService
            stream = StreamService()
            await stream.publish_event(
                session_id=session_id,
                event_type="step",
                data={
                    "id": str(log.id),
                    "agent_role": log.agent_role,
                    "step_name": log.step_name,
                    "status": log.status,
                    "message": log.message,
                    "step_order": log.step_order,
                    "step_metadata": log.step_metadata,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
            )
        except Exception:
            pass
        return log

    async def complete_step(
        self,
        log_id: uuid.UUID,
        duration_ms: float | None = None,
        token_count: int | None = None,
        message: str | None = None,
        step_metadata: dict[str, Any] | None = None,
    ) -> ExecutionLog | None:
        """
        Mark a step as completed, recording its duration and token usage.
        Called at the end of every agent action.
        """
        values: dict[str, Any] = {"status": "completed"}
        if duration_ms is not None:
            values["duration_ms"] = duration_ms
        if token_count is not None:
            values["token_count"] = token_count
        if message is not None:
            values["message"] = message
        if step_metadata is not None:
            values["step_metadata"] = step_metadata

        await self._session.execute(
            update(ExecutionLog)
            .where(ExecutionLog.id == log_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        await self._session.flush()
        updated_log = await self.get_by_id(log_id)
        
        if updated_log:
            try:
                from app.services.stream import StreamService
                stream = StreamService()
                await stream.publish_event(
                    session_id=updated_log.session_id,
                    event_type="step",
                    data={
                        "id": str(updated_log.id),
                        "agent_role": updated_log.agent_role,
                        "step_name": updated_log.step_name,
                        "status": updated_log.status,
                        "message": updated_log.message,
                        "step_order": updated_log.step_order,
                        "step_metadata": updated_log.step_metadata,
                        "duration_ms": updated_log.duration_ms,
                        "token_count": updated_log.token_count,
                        "created_at": updated_log.created_at.isoformat() if updated_log.created_at else None,
                    }
                )
            except Exception:
                pass
        return updated_log

    async def fail_step(
        self,
        log_id: uuid.UUID,
        error_detail: str,
        duration_ms: float | None = None,
    ) -> ExecutionLog | None:
        """Mark a step as failed with error details."""
        values: dict[str, Any] = {"status": "failed", "error_detail": error_detail}
        if duration_ms is not None:
            values["duration_ms"] = duration_ms

        await self._session.execute(
            update(ExecutionLog)
            .where(ExecutionLog.id == log_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        await self._session.flush()
        updated_log = await self.get_by_id(log_id)

        if updated_log:
            try:
                from app.services.stream import StreamService
                stream = StreamService()
                await stream.publish_event(
                    session_id=updated_log.session_id,
                    event_type="step",
                    data={
                        "id": str(updated_log.id),
                        "agent_role": updated_log.agent_role,
                        "step_name": updated_log.step_name,
                        "status": updated_log.status,
                        "message": updated_log.message,
                        "step_order": updated_log.step_order,
                        "step_metadata": updated_log.step_metadata,
                        "error_detail": updated_log.error_detail,
                        "duration_ms": updated_log.duration_ms,
                        "created_at": updated_log.created_at.isoformat() if updated_log.created_at else None,
                    }
                )
            except Exception:
                pass
        return updated_log

    async def count_by_status(self, session_id: uuid.UUID) -> dict[str, int]:
        """
        Return {status: count} for all steps in a session.
        Used to determine if a session is fully complete.
        """
        from sqlalchemy import func
        result = await self._session.execute(
            select(ExecutionLog.status, func.count(ExecutionLog.id))
            .where(ExecutionLog.session_id == session_id)
            .group_by(ExecutionLog.status)
        )
        return {row[0]: row[1] for row in result.all()}
