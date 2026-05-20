# ============================================
# Deep Research Platform - ExecutionLog Model
# ============================================
"""
Tracks individual agent execution steps within a ResearchSession.

WHY fine-grained logging:
- Enables real-time SSE progress streaming in Phase 5
- Provides per-step durations for performance profiling
- Makes retries and failures debuggable
- Drives the timeline UI in the frontend
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class ExecutionLog(UUIDMixin, TimestampMixin, Base):
    """
    A single agent step log within a research session.

    Each agent action (search, fetch, summarize, synthesize)
    produces one or more ExecutionLog rows that drive:
    - SSE progress events (Phase 5)
    - Agent timeline UI (Phase 6)
    - Audit/debugging (Phase 9)
    """

    __tablename__ = "execution_logs"

    # ---------- Foreign Key ----------
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent research session.",
    )

    # ---------- Agent Step Info ----------
    agent_role: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="The agent role executing this step (planner, researcher, etc.).",
    )
    step_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Human-readable name for this execution step.",
    )
    step_order: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Ordinal position of this step within the session. Used for ordering.",
    )

    # ---------- Status & Result ----------
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Step status: pending | running | completed | failed | skipped.",
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable progress message or error detail.",
    )
    error_detail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full exception trace or error context for failed steps.",
    )

    # ---------- Performance Metrics ----------
    duration_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Wall-clock duration of this step in milliseconds.",
    )
    token_count: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Tokens consumed by LLM calls in this step (for cost tracking).",
    )

    # ---------- Metadata ----------
    step_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Arbitrary step data: model params, source URLs, chunk counts, etc.",
    )

    # ---------- Relationship ----------
    session: Mapped["ResearchSession"] = relationship(  # noqa: F821
        "ResearchSession",
        back_populates="execution_logs",
    )

    # ---------- Indexes ----------
    __table_args__ = (
        # Fast fetch of all steps for a session in order
        Index("ix_execution_logs_session_id_order", "session_id", "step_order"),
        # Fast filter by status across all sessions (e.g., find all "running" steps)
        Index("ix_execution_logs_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ExecutionLog id={self.id} session={self.session_id} "
            f"step={self.step_name!r} status={self.status}>"
        )
