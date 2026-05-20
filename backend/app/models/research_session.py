# ============================================
# Deep Research Platform - ResearchSession Model
# ============================================
"""
Represents a single user-initiated research job.

WHY this is the central entity:
- Every agent execution, source fetch, and log entry
  is a child of a ResearchSession.
- Status tracks the full lifecycle from PENDING → COMPLETED.
- JSONB metadata allows flexible extra data without schema migrations.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ResearchStatus
from app.db.base import Base, TimestampMixin, UUIDMixin


class ResearchSession(UUIDMixin, TimestampMixin, Base):
    """
    Persistent record of a research session.

    Lifecycle:
        PENDING → PLANNING → RESEARCHING → WRITING → REVIEWING → COMPLETED
        Any state → FAILED | CANCELLED
    """

    __tablename__ = "research_sessions"

    # ---------- Core Fields ----------
    topic: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The research query or topic submitted by the user.",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ResearchStatus.PENDING,
        server_default=ResearchStatus.PENDING,
        comment="Current lifecycle status of the research session.",
    )

    # ---------- Result Fields ----------
    result_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Final synthesized research summary. Populated on COMPLETED.",
    )
    result_token_count: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Token count of the final result. Used for billing/observability.",
    )

    # ---------- Metadata ----------
    # Flexible bag for things like: model used, user agent, source count, etc.
    # Avoids adding columns for every future analytics field.
    session_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Arbitrary session metadata (model config, user context, etc.).",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if the session moved to FAILED state.",
    )

    # ---------- Relationships ----------
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(  # noqa: F821
        "ExecutionLog",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="select",
    )
    sources: Mapped[list["Source"]] = relationship(  # noqa: F821
        "Source",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ---------- Indexes ----------
    __table_args__ = (
        # Fast lookup by status (e.g., fetch all PENDING sessions)
        Index("ix_research_sessions_status", "status"),
        # Fast lookup by creation time for history/pagination
        Index("ix_research_sessions_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ResearchSession id={self.id} status={self.status} "
            f"topic={self.topic[:40]!r}>"
        )

    def is_terminal(self) -> bool:
        """Return True if the session is in a terminal (non-resumable) state."""
        return self.status in (
            ResearchStatus.COMPLETED,
            ResearchStatus.FAILED,
            ResearchStatus.CANCELLED,
        )
