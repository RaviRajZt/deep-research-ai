# ============================================
# Deep Research Platform - Application Lifecycle
# ============================================
# Manages startup and shutdown events.
#
# WHY a dedicated lifecycle module:
# - Single place to see all init/teardown logic
# - Ordered startup: logging → config → DB → Redis → DI
# - Graceful shutdown: close pools, flush logs
# - Easy to extend for future services
# ============================================

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.settings import get_settings
from app.db.session import async_engine, dispose_engine
from app.logging_.setup import setup_logging
from app.redis_.client import close_redis, init_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    Startup sequence:
    1. Configure structured logging
    2. Validate settings (fail-fast)
    3. Initialize database engine
    4. Initialize Redis connection pool
    5. Log successful startup

    Shutdown sequence:
    1. Close Redis connections
    2. Dispose database engine
    3. Log shutdown
    """
    settings = get_settings()

    # ---------- Startup ----------
    setup_logging(
        log_level=settings.log_level,
        environment=settings.app_env,
        app_name=settings.app_name,
    )
    logger.info(
        "Starting %s in %s mode",
        settings.app_name,
        settings.app_env,
    )

    # Initialize database engine (validates connection config)
    _ = async_engine(settings)
    logger.info("Database engine initialized")

    # Initialize Redis
    await init_redis(settings)
    logger.info("Redis connection pool initialized")

    logger.info("Application startup complete")

    yield  # Application runs here

    # ---------- Shutdown ----------
    logger.info("Shutting down application...")
    await close_redis()
    logger.info("Redis connections closed")

    await dispose_engine()
    logger.info("Database engine disposed")

    logger.info("Application shutdown complete")
