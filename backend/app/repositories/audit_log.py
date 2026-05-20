# ============================================
# Deep Research Platform - AuditLog Repository
# ============================================
"""
Append-only data access layer for AuditLog entities.

CRITICAL RULE: This repository intentionally does NOT expose
update() or delete() methods. AuditLogs are immutable by design.
Overriding the inherited methods raises an error if called.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import SQLAlchemyRepository


class AuditLogRepository(SQLAlchemyRepository[AuditLog]):
    """
    Append-only repository for AuditLog.

    Inherited update() and delete() are intentionally disabled.
    """

    model = AuditLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ------------------------------------------------------------------
    # Immutability Guards
    # ------------------------------------------------------------------

    async def update(self, entity_id: uuid.UUID, **kwargs: Any) -> None:  # type: ignore[override]
        raise NotImplementedError(
            "AuditLog records are immutable. update() is not permitted."
        )

    async def delete(self, entity_id: uuid.UUID) -> None:  # type: ignore[override]
        raise NotImplementedError(
            "AuditLog records are immutable. delete() is not permitted."
        )

    # ------------------------------------------------------------------
    # Append Methods
    # ------------------------------------------------------------------

    async def log_insert(
        self,
        table_name: str,
        record_id: uuid.UUID,
        new_values: dict[str, Any],
        changed_by: str | None = None,
        request_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append an INSERT audit event."""
        return await self.create(
            table_name=table_name,
            record_id=record_id,
            action="INSERT",
            changed_by=changed_by,
            new_values=new_values,
            previous_values=None,
            request_id=request_id,
            extra=extra,
        )

    async def log_update(
        self,
        table_name: str,
        record_id: uuid.UUID,
        previous_values: dict[str, Any],
        new_values: dict[str, Any],
        changed_by: str | None = None,
        request_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append an UPDATE audit event with before/after diff."""
        return await self.create(
            table_name=table_name,
            record_id=record_id,
            action="UPDATE",
            changed_by=changed_by,
            previous_values=previous_values,
            new_values=new_values,
            request_id=request_id,
            extra=extra,
        )

    async def log_delete(
        self,
        table_name: str,
        record_id: uuid.UUID,
        previous_values: dict[str, Any],
        changed_by: str | None = None,
        request_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append a DELETE audit event with last-known values."""
        return await self.create(
            table_name=table_name,
            record_id=record_id,
            action="DELETE",
            changed_by=changed_by,
            previous_values=previous_values,
            new_values=None,
            request_id=request_id,
            extra=extra,
        )

    # ------------------------------------------------------------------
    # Query Methods
    # ------------------------------------------------------------------

    async def get_by_record(
        self,
        table_name: str,
        record_id: uuid.UUID,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Return full audit history for a specific record, oldest first."""
        result = await self._session.execute(
            select(AuditLog)
            .where(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id,
            )
            .order_by(AuditLog.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 100) -> list[AuditLog]:
        """Return the most recent audit events across all tables."""
        result = await self._session.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
