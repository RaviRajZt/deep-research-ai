# ============================================
# Deep Research Platform - AuditLog Model
# ============================================
"""
Immutable audit trail for all significant data mutations.

WHY a dedicated audit table:
- Provides a tamper-evident history of who changed what and when
- Required for production compliance and debugging
- Separate from execution_logs (those track agent steps; this tracks data changes)
- Append-only — rows are NEVER updated or deleted (enforced by repository layer)
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin


class AuditLog(UUIDMixin, Base):
    """
    Append-only audit record for data mutations.

    WHY no TimestampMixin (updated_at):
    - AuditLog rows are immutable — they are never updated.
    - Only created_at is needed. updated_at would be misleading.
    """

    __tablename__ = "audit_logs"

    # ---------- What Changed ----------
    table_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="The table that was mutated (e.g. 'research_sessions').",
    )
    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Primary key of the mutated record.",
    )
    action: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="Mutation type: INSERT | UPDATE | DELETE.",
    )

    # ---------- Who / When ----------
    # changed_by is nullable now — auth is a future phase.
    # Once auth lands, populate this from the request context.
    changed_by: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        comment="User or service identity that triggered the change. Nullable until auth is implemented.",
    )
    created_at: Mapped[str] = mapped_column(
        nullable=False,
        server_default="NOW()",
        comment="Timestamp of the audit event (UTC).",
    )

    # ---------- What Changed (Diff) ----------
    previous_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Snapshot of field values BEFORE the mutation. Null for INSERT.",
    )
    new_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Snapshot of field values AFTER the mutation. Null for DELETE.",
    )

    # ---------- Context ----------
    request_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Correlation/request ID from the HTTP request that triggered the change.",
    )
    extra: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Arbitrary extra context (IP address, user-agent, feature flag states, etc.).",
    )

    # ---------- Indexes ----------
    __table_args__ = (
        # Most common query: all audit events for a specific record
        Index("ix_audit_logs_table_record", "table_name", "record_id"),
        # Chronological audit trail lookup
        Index("ix_audit_logs_created_at", "created_at"),
        # Filter by action type (e.g., find all DELETEs)
        Index("ix_audit_logs_action", "action"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action} "
            f"table={self.table_name!r} record={self.record_id}>"
        )
