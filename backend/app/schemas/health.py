# ============================================
# Deep Research Platform - Health Check Schemas
# ============================================

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.enums import HealthStatus


class ServiceHealthSchema(BaseModel):
    """Health status of a single infrastructure service."""

    name: str = Field(description="Service name (e.g., postgres, redis)")
    status: HealthStatus
    latency_ms: float | None = Field(
        default=None,
        description="Round-trip latency in milliseconds",
    )
    error: str | None = Field(
        default=None,
        description="Error message if unhealthy",
    )


class HealthCheckResponse(BaseModel):
    """Full health check response including all services."""

    status: HealthStatus = Field(
        description="Overall platform health (healthy/degraded/unhealthy)"
    )
    version: str = Field(description="Application version")
    environment: str = Field(description="Current deployment environment")
    services: list[ServiceHealthSchema] = Field(
        default_factory=list,
        description="Health status of each infrastructure service",
    )


class ReadinessResponse(BaseModel):
    """Kubernetes readiness probe response."""

    ready: bool
    checks: dict[str, bool] = Field(default_factory=dict)
