# ============================================
# Deep Research Platform - Redis Cache Service
# ============================================
"""
High-level cache abstraction over the Redis client.

WHY an abstraction layer:
- Enforces namespace isolation via key prefixing
- Centralizes TTL strategy
- Provides typed get/set helpers
- Enables swapping Redis for another cache without changing callers
- Handles serialization/deserialization uniformly
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from app.core.constants import (
    CACHE_TTL_MEDIUM,
    REDIS_NS_CACHE,
)
from app.core.settings import get_settings
from app.redis_.client import get_redis_client

logger = logging.getLogger(__name__)
T = TypeVar("T")


class CacheService:
    """
    General-purpose cache service using Redis.

    Key format: {global_prefix}:{namespace}:{key}
    Example:    dr:cache:research:abc123

    TTL Tiers (use constants from app.core.constants):
    - CACHE_TTL_SHORT    = 60s   (volatile data)
    - CACHE_TTL_MEDIUM   = 300s  (API responses)
    - CACHE_TTL_LONG     = 3600s (expensive computations)
    - CACHE_TTL_VERY_LONG = 86400s (static data)
    """

    def __init__(
        self,
        namespace: str = REDIS_NS_CACHE,
    ) -> None:
        settings = get_settings()
        self._prefix = settings.redis_key_prefix
        self._namespace = namespace
        self._default_ttl = settings.redis_default_ttl

    def _build_key(self, key: str) -> str:
        """Build namespaced Redis key."""
        return f"{self._prefix}:{self._namespace}:{key}"

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from cache.

        Returns:
            Deserialized value or None if missing/expired.
        """
        client = get_redis_client()
        full_key = self._build_key(key)
        try:
            raw = await client.get(full_key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Cache get failed", extra={"key": full_key}, exc_info=exc)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Store a value in cache with optional TTL.

        Args:
            key: Cache key (will be namespaced)
            value: JSON-serializable value
            ttl: TTL in seconds; defaults to redis_default_ttl setting

        Returns:
            True if set successfully.
        """
        client = get_redis_client()
        full_key = self._build_key(key)
        effective_ttl = ttl if ttl is not None else self._default_ttl
        try:
            serialized = json.dumps(value, default=str)
            await client.setex(full_key, effective_ttl, serialized)
            return True
        except Exception as exc:
            logger.warning("Cache set failed", extra={"key": full_key}, exc_info=exc)
            return False

    async def delete(self, key: str) -> bool:
        """Remove a key from cache."""
        client = get_redis_client()
        full_key = self._build_key(key)
        try:
            deleted = await client.delete(full_key)
            return bool(deleted)
        except Exception as exc:
            logger.warning("Cache delete failed", extra={"key": full_key}, exc_info=exc)
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        client = get_redis_client()
        full_key = self._build_key(key)
        try:
            return bool(await client.exists(full_key))
        except Exception as exc:
            logger.warning("Cache exists failed", extra={"key": full_key}, exc_info=exc)
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Update TTL for an existing key."""
        client = get_redis_client()
        full_key = self._build_key(key)
        try:
            return bool(await client.expire(full_key, ttl))
        except Exception as exc:
            logger.warning("Cache expire failed", extra={"key": full_key}, exc_info=exc)
            return False

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: int = CACHE_TTL_MEDIUM,
    ) -> Any:
        """
        Cache-aside pattern: return cached value or compute and store.

        Args:
            key: Cache key
            factory: Async callable that produces the value on cache miss
            ttl: TTL in seconds for the stored value

        Usage:
            value = await cache.get_or_set(
                "my-key",
                lambda: expensive_async_operation(),
                ttl=CACHE_TTL_LONG,
            )
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await factory()
        await self.set(key, value, ttl=ttl)
        return value
