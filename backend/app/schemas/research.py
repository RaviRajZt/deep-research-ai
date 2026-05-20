# ============================================
# Deep Research Platform - Research Schemas
# ============================================
"""
Pydantic schemas for ResearchSession request/response contracts.

WHY separate schemas from ORM models:
- ORM models define persistence structure
- Schemas define API contract (what clients send/receive)
- Decouples API shape from DB shape (can evolve independently)
- Enables field filtering (e.g., never expose internal fields)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.core.enums import ResearchStatus
from app.schemas.base import BaseSchema, TimestampedSchema


# ------------------------------------------------------------------
# Request Schemas
# ------------------------------------------------------------------

class ResearchSessionCreate(BaseSchema):
    """Schema for creating a new research session."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Research query or topic to investigate.",
        examples=["Impact of quantum computing on cryptography"],
    )
    session_metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional context metadata (e.g., requested model, source limits).",
    )


class ResearchSessionStatusUpdate(BaseSchema):
    """Schema for manually updating a session status (admin/internal use)."""

    status: ResearchStatus
    error_message: str | None = None


# ------------------------------------------------------------------
# Response Schemas
# ------------------------------------------------------------------

class ResearchSessionResponse(TimestampedSchema):
    """Full research session response — returned by GET /sessions/{id}."""

    id: uuid.UUID
    topic: str
    status: ResearchStatus
    result_summary: str | None = None
    result_token_count: int | None = None
    error_message: str | None = None
    session_metadata: dict[str, Any] | None = None

    class Config:
        from_attributes = True  # Enable ORM → schema conversion


class ResearchSessionListResponse(BaseSchema):
    """Paginated list of research sessions."""

    items: list[ResearchSessionResponse]
    total: int
    limit: int
    offset: int


class ResearchSessionSummary(BaseSchema):
    """Lightweight summary for list views — omits large text fields."""

    id: uuid.UUID
    topic: str
    status: ResearchStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
