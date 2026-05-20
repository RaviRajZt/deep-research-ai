# ============================================
# Deep Research Platform - Source Model
# ============================================
"""
Tracks every web source fetched during a research session.

WHY a dedicated Source table:
- Enables deduplication across sessions (via content_hash)
- Tracks fetch status independently from session status
- Stores token counts for LLM budget tracking
- Source list drives the "References" section of the final report
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Source(UUIDMixin, TimestampMixin, Base):
    """
    A single web source associated with a research session.

    Fetch status lifecycle:
        pending → fetching → fetched → failed | skipped
    """

    __tablename__ = "sources"

    # ---------- Foreign Key ----------
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent research session.",
    )

    # ---------- Source Identity ----------
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full URL of the fetched source.",
    )
    domain: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        index=True,
        comment="Extracted domain for grouping/filtering (e.g. 'arxiv.org').",
    )
    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Page title extracted from HTML.",
    )

    # ---------- Content Tracking ----------
    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="SHA-256 of raw content. Enables cross-session deduplication.",
    )
    fetch_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="Fetch lifecycle: pending | fetching | fetched | failed | skipped.",
    )
    fetch_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error detail if fetch_status is 'failed'.",
    )

    # ---------- Token Accounting ----------
    # CRITICAL: Stored separately from content — we NEVER persist raw content.
    # Only summaries and token counts are stored per PROJECT_DETAILS token safety rules.
    raw_token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated token count of raw fetched content (before chunking).",
    )
    summary_token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Token count of the generated source summary.",
    )
    chunk_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of content chunks produced from this source.",
    )

    # ---------- Metadata ----------
    source_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Arbitrary source metadata: HTTP status, content-type, language, etc.",
    )

    # ---------- Relationship ----------
    session: Mapped["ResearchSession"] = relationship(  # noqa: F821
        "ResearchSession",
        back_populates="sources",
    )

    # ---------- Indexes ----------
    __table_args__ = (
        # Fast source listing per session
        Index("ix_sources_session_id_fetch_status", "session_id", "fetch_status"),
        # Cross-session dedup lookup
        Index("ix_sources_content_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        return (
            f"<Source id={self.id} domain={self.domain!r} "
            f"fetch_status={self.fetch_status}>"
        )
