# ============================================
# Deep Research Platform - Health Check API Router
# ============================================
"""
Health and readiness endpoints for infrastructure probes.

Endpoints:
  GET /api/v1/health   — Full health check (Postgres + Redis + version)
  GET /api/v1/ready    — Minimal readiness probe (used by K8s/Docker)
  GET /api/v1/flags    — Feature flag states (dev/staging only)
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.enums import HealthStatus
from app.core.feature_flags import feature_flags
from app.core.settings import get_settings
from app.schemas.health import HealthCheckResponse, ReadinessResponse
from app.services.health import HealthService

router = APIRouter(prefix="/health", tags=["Health"])
_health_service = HealthService()


@router.get(
    "",
    response_model=HealthCheckResponse,
    summary="Full health check",
    description="Returns health status of all platform services (Postgres, Redis).",
)
async def health_check() -> HealthCheckResponse:
    """
    Full platform health check.

    Checks connectivity to all infrastructure services.
    Returns HTTP 503 if any critical service (Postgres) is down.
    """
    result = await _health_service.get_full_health()

    if result.status == HealthStatus.UNHEALTHY:
        raise HTTPException(
            status_code=503,
            detail={
                "status": result.status,
                "services": [s.model_dump() for s in result.services],
            },
        )

    return result


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Lightweight readiness check for container orchestrators.",
)
async def readiness_probe() -> ReadinessResponse:
    """
    Kubernetes/Docker readiness probe.

    Returns HTTP 503 if the app is not ready to serve traffic.
    Faster than /health — skips non-critical checks.
    """
    result = await _health_service.get_readiness()

    if not result.ready:
        raise HTTPException(status_code=503, detail="Service not ready")

    return result


@router.get(
    "/flags",
    summary="Feature flag states",
    description="Returns current feature flag configuration. Restricted in production.",
)
async def get_feature_flags() -> dict:
    """
    Expose current feature flag states.

    Only accessible in development and staging environments.
    """
    settings = get_settings()
    if settings.is_production:
        raise HTTPException(
            status_code=403,
            detail="Feature flag endpoint not available in production",
        )

    return feature_flags.to_dict()
