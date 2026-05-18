# ============================================
# Deep Research Platform - Health Check Service
# ============================================
"""
Aggregates health status of all infrastructure services.

WHY a dedicated health service:
- Separates health logic from HTTP layer
- Reusable in readiness/liveness endpoints
- Easy to extend with new service checks
- Structured results for observability systems
"""

from __future__ import annotations

import logging
import time

from sqlalchemy import text

from app.core.enums import HealthStatus, ServiceName
from app.core.settings import get_settings
from app.db.session import async_engine
from app.redis_.client import check_redis_health
from app.schemas.health import HealthCheckResponse, ReadinessResponse, ServiceHealthSchema

logger = logging.getLogger(__name__)


class HealthService:
    """Checks and aggregates health of all platform services."""

    async def check_postgres(self) -> ServiceHealthSchema:
        """Verify PostgreSQL connectivity with a lightweight query."""
        settings = get_settings()
        start = time.perf_counter()
        try:
            engine = async_engine(settings)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ServiceHealthSchema(
                name=ServiceName.POSTGRES,
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
            )
        except Exception as exc:
            logger.warning("PostgreSQL health check failed", exc_info=exc)
            return ServiceHealthSchema(
                name=ServiceName.POSTGRES,
                status=HealthStatus.UNHEALTHY,
                error=str(exc),
            )

    async def check_redis(self) -> ServiceHealthSchema:
        """Verify Redis connectivity via PING."""
        start = time.perf_counter()
        healthy = await check_redis_health()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        return ServiceHealthSchema(
            name=ServiceName.REDIS,
            status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
            latency_ms=latency_ms if healthy else None,
            error=None if healthy else "Redis PING failed",
        )

    async def get_full_health(self) -> HealthCheckResponse:
        """
        Run all health checks and return aggregated status.

        Overall status logic:
        - HEALTHY: all services healthy
        - DEGRADED: some services unhealthy (non-critical)
        - UNHEALTHY: critical services (postgres) are down
        """
        from app import __version__

        settings = get_settings()
        services = [
            await self.check_postgres(),
            await self.check_redis(),
        ]

        # Determine overall status
        unhealthy = [s for s in services if s.status == HealthStatus.UNHEALTHY]
        if not unhealthy:
            overall = HealthStatus.HEALTHY
        elif any(s.name == ServiceName.POSTGRES for s in unhealthy):
            overall = HealthStatus.UNHEALTHY  # Postgres is critical
        else:
            overall = HealthStatus.DEGRADED   # Non-critical services down

        return HealthCheckResponse(
            status=overall,
            version=__version__,
            environment=settings.app_env,
            services=services,
        )

    async def get_readiness(self) -> ReadinessResponse:
        """
        Minimal readiness check for Kubernetes probes.
        Returns ready=True only if all critical services are healthy.
        """
        postgres = await self.check_postgres()
        redis = await self.check_redis()

        checks = {
            ServiceName.POSTGRES: postgres.status == HealthStatus.HEALTHY,
            ServiceName.REDIS: redis.status == HealthStatus.HEALTHY,
        }
        ready = checks[ServiceName.POSTGRES]  # Postgres is the critical dependency

        return ReadinessResponse(ready=ready, checks=checks)
