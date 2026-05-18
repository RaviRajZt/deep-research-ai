# ============================================
# Deep Research Platform - Repository Base Classes
# ============================================
"""
Generic repository pattern for data access abstraction.

WHY repository pattern:
- Decouples business logic from ORM implementation
- Enables unit testing with mock repositories
- Single source of truth for data access patterns
- Swappable storage backends (PostgreSQL → NoSQL)
- Consistent CRUD interface across all entities
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class AbstractRepository(ABC, Generic[ModelT]):
    """
    Abstract base repository defining the standard data access contract.

    All concrete repositories must implement these methods.
    This enables dependency inversion — services depend on the
    abstract interface, not the concrete SQLAlchemy implementation.
    """

    @abstractmethod
    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None: ...

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]: ...

    @abstractmethod
    async def create(self, **kwargs: Any) -> ModelT: ...

    @abstractmethod
    async def update(self, entity_id: uuid.UUID, **kwargs: Any) -> ModelT | None: ...

    @abstractmethod
    async def delete(self, entity_id: uuid.UUID) -> bool: ...


class SQLAlchemyRepository(AbstractRepository[ModelT], Generic[ModelT]):
    """
    Concrete SQLAlchemy implementation of the repository pattern.

    Provides default CRUD operations that concrete repositories
    can inherit and override as needed.

    Usage:
        class UserRepository(SQLAlchemyRepository[User]):
            model = User

            async def get_by_email(self, email: str) -> User | None:
                result = await self._session.execute(
                    select(self.model).where(User.email == email)
                )
                return result.scalar_one_or_none()
    """

    model: type[ModelT]  # Must be set by subclasses

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        """Retrieve entity by primary key UUID."""
        result = await self._session.execute(
            select(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """Retrieve paginated list of all entities."""
        result = await self._session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelT:
        """Create and persist a new entity."""
        instance = self.model(**kwargs)
        self._session.add(instance)
        await self._session.flush()   # Get DB-generated values (e.g., UUID)
        await self._session.refresh(instance)
        return instance

    async def update(self, entity_id: uuid.UUID, **kwargs: Any) -> ModelT | None:
        """Update entity fields and return updated instance."""
        instance = await self.get_by_id(entity_id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, entity_id: uuid.UUID) -> bool:
        """Delete entity by ID. Returns True if deleted, False if not found."""
        instance = await self.get_by_id(entity_id)
        if instance is None:
            return False
        await self._session.delete(instance)
        await self._session.flush()
        return True
