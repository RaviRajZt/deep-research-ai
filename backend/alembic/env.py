# ============================================
# Deep Research Platform - Alembic env.py
# ============================================
"""
Alembic migration environment.

WHY async-based env.py:
- Consistent with async SQLAlchemy throughout the app
- Uses the same engine configuration as the application
- URL loaded from Pydantic settings (single source of truth)
- Target metadata from Base enables autogenerate support
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import Base so Alembic can detect model changes for autogenerate
from app.db.base import Base
from app.core.settings import get_settings

# Alembic Config object
config = context.config

# Inject database URL from application settings (overrides alembic.ini)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Setup stdlib logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate (detects model changes)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without a live DB connection.
    Outputs SQL statements to stdout instead.
    Used for generating SQL scripts for review.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations with async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
