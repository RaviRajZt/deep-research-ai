# ============================================
# Deep Research Platform - Shared API Schemas
# ============================================
"""
Pydantic v2 schemas shared across multiple API endpoints.

WHY separate schemas from models:
- API contracts are independent of DB schema
- Enables versioning without touching DB models
- Allows selective field exposure (no accidental data leaks)
- Pydantic v2 validation is request-layer concern
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Base class for all Pydantic schemas.

    Configuration:
    - from_attributes=True: Enables ORM mode (SQLAlchemy model → schema)
    - populate_by_name=True: Allow field population by Python name or alias
    - str_strip_whitespace=True: Auto-strip whitespace from string fields
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page (max 100)",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic wrapper for paginated list responses.

    Usage:
        @router.get("/items", response_model=PaginatedResponse[ItemSchema])
        async def list_items(...):
            return PaginatedResponse(items=items, total=total, page=1, page_size=20)
    """

    items: list[T]
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        total_pages = max(1, -(-total // page_size))  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorDetail(BaseModel):
    """Structured error response body."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Top-level error response envelope."""

    error: ErrorDetail


class SuccessResponse(BaseModel):
    """Simple success acknowledgement response."""

    success: bool = True
    message: str = "Operation completed successfully"


class TimestampedSchema(BaseSchema):
    """
    Base schema for entities that have created_at / updated_at fields.
    All DB response schemas for timestamped models should inherit from this.
    """

    created_at: datetime
    updated_at: datetime
