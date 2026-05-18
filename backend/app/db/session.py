# ============================================
# Deep Research Platform - Database Session Management
# ============================================
"""
Async SQLAlchemy engine and session factory.

WHY this design:
- Single engine per process (connection pooling)
- Scoped async sessions per request (no shared state)
- Dependency injection via FastAPI Depends
- Transaction management via context manager
- Clean separation from business logic
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from app.core import AppSettings

logger = logging.getLogger(__name__)

# Module-level references managed by lifecycle
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def async_engine(settings: AppSettings) -> AsyncEngine:
    """
    Create or return the async SQLAlchemy engine.

    Uses connection pooling with configurable pool size and overflow.
    The engine is created once and reused for the process lifetime.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.postgres_echo,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_pre_ping=True,           # Validate connections before use
            pool_recycle=300,             # Recycle connections every 5 minutes
            connect_args={
                "server_settings": {
                    "application_name": settings.app_name,
                },
            },
        )
        logger.info(
            "Database engine created",
            extra={
                "pool_size": settings.postgres_pool_size,
                "max_overflow": settings.postgres_max_overflow,
            },
        )
    return _engine


def get_session_factory(settings: AppSettings) -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.

    Sessions are configured with:
    - expire_on_commit=False: Prevents lazy loading issues after commit
    - autoflush=False: Explicit flush for predictable behavior
    """
    global _session_factory
    if _session_factory is None:
        engine = async_engine(settings)
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


async def get_db_session(
    settings: AppSettings | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.

    Usage:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            ...

    The session is automatically closed after the request completes.
    Transactions are committed on success, rolled back on exception.
    """
    if settings is None:
        from app.core.settings import get_settings
        settings = get_settings()

    factory = get_session_factory(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
    """
    Dispose the engine and close all pooled connections.
    Called during application shutdown.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine disposed")
