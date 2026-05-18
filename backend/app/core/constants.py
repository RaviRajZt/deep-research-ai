# ============================================
# Deep Research Platform - Application Constants
# ============================================
# Immutable values used across the application.
#
# WHY separate from settings:
# Constants are compile-time values that never change per environment.
# Settings are runtime values that vary by deployment.
# ============================================

from __future__ import annotations

from typing import Final

# ---------- API ----------
API_V1_PREFIX: Final[str] = "/api/v1"
API_TITLE: Final[str] = "Deep Research Platform"
API_DESCRIPTION: Final[str] = (
    "Enterprise AI Research Agent Platform — "
    "Multi-agent research orchestration with real-time streaming."
)
API_VERSION: Final[str] = "0.1.0"

# ---------- Headers ----------
HEADER_REQUEST_ID: Final[str] = "X-Request-ID"
HEADER_CORRELATION_ID: Final[str] = "X-Correlation-ID"

# ---------- Pagination ----------
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# ---------- Cache TTLs (seconds) ----------
CACHE_TTL_SHORT: Final[int] = 60          # 1 minute
CACHE_TTL_MEDIUM: Final[int] = 300        # 5 minutes
CACHE_TTL_LONG: Final[int] = 3600         # 1 hour
CACHE_TTL_VERY_LONG: Final[int] = 86400   # 24 hours

# ---------- Database ----------
DB_NAMING_CONVENTION: Final[dict[str, str]] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# ---------- Redis Key Namespaces ----------
# Format: {prefix}:{namespace}:{key}
REDIS_NS_CACHE: Final[str] = "cache"
REDIS_NS_SESSION: Final[str] = "session"
REDIS_NS_RATE_LIMIT: Final[str] = "rl"
REDIS_NS_FEATURE_FLAG: Final[str] = "ff"
REDIS_NS_AGENT_STATE: Final[str] = "agent"

# ---------- Date/Time ----------
DATETIME_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S.%fZ"

# ---------- Health Check ----------
HEALTH_CHECK_TIMEOUT: Final[int] = 5  # seconds
