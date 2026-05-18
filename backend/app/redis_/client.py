# ============================================
# Deep Research Platform - Redis Client Manager
# ============================================
"""
Async Redis connection pool management.

WHY this design:
- Single connection pool per process (not per request)
- Reusable client instance with typed helpers
- Namespace isolation to prevent key collisions
- TTL strategy enforced at the abstraction layer
- Async-compatible via redis.asyncio
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

if TYPE_CHECKING:
    from app.core import AppSettings

logger = logging.getLogger(__name__)

# Module-level pool/client managed by lifecycle hooks
_pool: ConnectionPool | None = None
_client: Redis | None = None  # type: ignore[type-arg]


async def init_redis(settings: AppSettings) -> None:
    """
    Initialize Redis connection pool.
    Called during application startup (lifespan).

    Connection pool is shared across all requests — not per-request.
    """
    global _pool, _client

    pool_kwargs: dict[str, Any] = {
        "host": settings.redis_host,
        "port": settings.redis_port,
        "db": settings.redis_db,
        "max_connections": settings.redis_max_connections,
        "decode_responses": True,           # Return str not bytes
        "socket_connect_timeout": 5,        # Fail fast on connect
        "socket_timeout": 5,                # Fail fast on operations
        "health_check_interval": 30,        # Periodic connection validation
    }

    password = settings.redis_password.get_secret_value()
    if password:
        pool_kwargs["password"] = password

    _pool = ConnectionPool(**pool_kwargs)
    _client = aioredis.Redis(connection_pool=_pool)

    # Verify connection immediately
    await _client.ping()
    logger.info(
        "Redis initialized",
        extra={
            "host": settings.redis_host,
            "port": settings.redis_port,
            "db": settings.redis_db,
        },
    )


def get_redis_client() -> Redis:  # type: ignore[type-arg]
    """
    Get the active Redis client.

    Raises:
        RuntimeError: If called before init_redis()
    """
    if _client is None:
        raise RuntimeError(
            "Redis client is not initialized. "
            "Ensure init_redis() is called during application startup."
        )
    return _client


async def close_redis() -> None:
    """
    Close all Redis connections gracefully.
    Called during application shutdown (lifespan).
    """
    global _pool, _client
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
    logger.info("Redis connections closed")


async def check_redis_health() -> bool:
    """
    Ping Redis and return True if healthy.
    Used by health check endpoints.
    """
    try:
        client = get_redis_client()
        response = await client.ping()
        return response is True
    except Exception as exc:
        logger.warning("Redis health check failed", exc_info=exc)
        return False
