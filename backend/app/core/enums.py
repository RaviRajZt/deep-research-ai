# ============================================
# Deep Research Platform - Application Enums
# ============================================
# Centralized enumeration types for type-safe constants.
#
# WHY enums instead of string literals:
# - IDE autocompletion
# - Compile-time validation
# - Prevents typos
# - Self-documenting
# - Easy refactoring
# ============================================

from __future__ import annotations

from enum import StrEnum, unique


@unique
class Environment(StrEnum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@unique
class LogLevel(StrEnum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@unique
class HealthStatus(StrEnum):
    """Health check status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@unique
class ServiceName(StrEnum):
    """
    Names of infrastructure services checked in health probes.
    Extend this as new services are added.
    """

    POSTGRES = "postgres"
    REDIS = "redis"
    API = "api"


# ---------- Future Phase Enums ----------
# These are defined now so the type system is ready when
# agent logic and research features are implemented.


@unique
class AgentRole(StrEnum):
    """
    Roles of AI agents in the research pipeline.
    Will be used by LangGraph orchestration in future phases.
    """

    PLANNER = "planner"
    RESEARCHER = "researcher"
    WRITER = "writer"
    REVIEWER = "reviewer"
    SYNTHESIZER = "synthesizer"


@unique
class ResearchStatus(StrEnum):
    """
    Status of a research session.
    Maps to database state and SSE event types.
    """

    PENDING = "pending"
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING = "writing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@unique
class SSEEventType(StrEnum):
    """
    Server-Sent Event type identifiers.
    Will be used as the `event:` field in SSE messages.
    """

    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    RESEARCH_UPDATE = "research_update"
    HEARTBEAT = "heartbeat"
