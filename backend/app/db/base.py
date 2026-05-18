# ============================================
# Deep Research Platform - SQLAlchemy Base Model
# ============================================
"""
Declarative base for all database models.

WHY a custom base:
- Enforces naming conventions for constraints/indexes
- Provides common columns (id, created_at, updated_at)
- Single source of truth for metadata
- Required by Alembic for autogenerate
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import MetaData, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.constants import DB_NAMING_CONVENTION


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Includes:
    - Naming convention for auto-generated constraints
    - Abstract base prevents direct table creation
    """

    metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)


class TimestampMixin:
    """
    Mixin providing created_at and updated_at timestamp columns.

    WHY a mixin instead of putting this in Base:
    - Not all tables need timestamps (e.g., association tables)
    - Explicit is better than implicit
    - Can be composed with other mixins
    """

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=text("NOW()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        nullable=False,
    )


class UUIDMixin:
    """
    Mixin providing a UUID primary key column.

    WHY UUIDs over auto-increment:
    - No sequential ID enumeration (security)
    - Safe for distributed ID generation
    - Can be generated client-side
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
