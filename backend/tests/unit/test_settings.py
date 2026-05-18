# ============================================
# Deep Research Platform - Settings Unit Tests
# ============================================

from __future__ import annotations

from app.core import AppSettings, get_settings


def test_get_settings_returns_singleton():
    """get_settings() must return the same cached instance on every call."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_default_settings_are_valid():
    """Default settings should produce a valid AppSettings instance."""
    settings = AppSettings()
    assert settings.app_name == "deep-research"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.postgres_pool_size > 0


def test_database_url_is_async():
    """database_url must use asyncpg driver for async SQLAlchemy."""
    settings = AppSettings()
    assert "asyncpg" in settings.database_url


def test_database_url_sync_uses_psycopg():
    """database_url_sync must NOT use asyncpg (used by Alembic)."""
    settings = AppSettings()
    assert "asyncpg" not in settings.database_url_sync


def test_redis_url_format():
    """Redis URL must be a valid redis:// scheme."""
    settings = AppSettings()
    assert settings.redis_url.startswith("redis://")


def test_environment_flags():
    """Environment property helpers are mutually exclusive."""
    settings = AppSettings(app_env="development")
    assert settings.is_development
    assert not settings.is_production
    assert not settings.is_staging
