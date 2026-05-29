# ============================================
# Deep Research Platform - Application Settings
# ============================================
# Centralized, validated configuration using Pydantic Settings.
#
# WHY Pydantic Settings:
# - Automatic environment variable loading
# - Type coercion and validation at startup (fail-fast)
# - Nested config models for logical grouping
# - IDE autocompletion and type checking
#
# Configuration hierarchy (highest priority first):
# 1. Environment variables
# 2. .env file
# 3. Default values defined here
# ============================================

from __future__ import annotations

from functools import lru_cache
from typing import Literal, cast

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
AppEnv = Literal["development", "staging", "production"]


class AppSettings(BaseSettings):
    """Core application settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- Application ----------
    app_name: str = Field(default="deep-research", description="Application name")
    app_env: AppEnv = Field(
        default="development",
        description="Current deployment environment",
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: LogLevel = Field( 
        default=cast(LogLevel, "INFO"),
        description="Logging level",
    )

    # ---------- API ----------
    backend_host: str = Field(default="0.0.0.0", description="Backend bind host")
    backend_port: int = Field(default=8000, description="Backend bind port")
    backend_workers: int = Field(default=1, description="Number of uvicorn workers")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 route prefix")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # ---------- Security ----------
    secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        description="Application secret key",
    )

    # ---------- PostgreSQL ----------
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_user: str = Field(default="deep_research")
    postgres_password: SecretStr = Field(default=SecretStr("deep_research_dev"))
    postgres_db: str = Field(default="deep_research")
    postgres_pool_size: int = Field(
        default=10,
        description="SQLAlchemy connection pool size",
    )
    postgres_max_overflow: int = Field(
        default=20,
        description="Max overflow connections beyond pool_size",
    )
    postgres_echo: bool = Field(
        default=False,
        description="Echo SQL statements (debug only)",
    )

    # ---------- Redis ----------
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_password: SecretStr = Field(default=SecretStr(""))
    redis_max_connections: int = Field(default=20)
    redis_default_ttl: int = Field(
        default=3600,
        description="Default cache TTL in seconds",
    )
    redis_key_prefix: str = Field(
        default="dr",
        description="Global Redis key prefix for namespace isolation",
    )

    # ---------- AI / LLM (future phase) ----------
    openai_api_key: SecretStr = Field(default=SecretStr(""))
    openai_model: str = Field(default="gpt-4o")
    openai_max_tokens: int = Field(default=4096)
    openai_temperature: float = Field(default=0.7)

    # ---------- Ollama / Local LLM ----------
    ollama_base_url: str = Field(default="http://localhost:11434/v1")
    ollama_model: str = Field(default="gemma2:2b")

    # ---------- SearXNG Search ----------
    searxng_base_url: str = Field(default="http://localhost:8080")

    # ---------- SSE (future phase) ----------
    sse_retry_timeout: int = Field(
        default=3000,
        description="SSE client retry timeout in milliseconds",
    )
    sse_max_connections: int = Field(default=100)

    # ---------- Rate Limiting ----------
    rate_limit_enabled: bool = Field(default=False)
    rate_limit_requests_per_minute: int = Field(default=60)

    # ---------- Computed Properties ----------

    @property
    def database_url(self) -> str:
        """Build async PostgreSQL connection URL."""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Build sync PostgreSQL URL (for Alembic migrations)."""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        password = self.redis_password.get_secret_value()
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_staging(self) -> bool:
        return self.app_env == "staging"

    # ---------- Validators ----------

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from JSON string or list."""
        if isinstance(v, str):
            import json

            return json.loads(v)  # type: ignore[no-any-return]
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(
        cls, v: str
    ) -> LogLevel:
        return cast(
            LogLevel,
            v.upper(),
        )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """
    Get cached application settings singleton.

    WHY lru_cache: Settings are immutable after startup. Caching avoids
    re-reading environment variables and .env file on every access.
    The cache is process-scoped, so each worker gets its own instance.
    """
    return AppSettings()
