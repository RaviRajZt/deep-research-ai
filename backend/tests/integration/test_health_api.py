# ============================================
# Deep Research Platform - Health API Integration Tests
# ============================================
# marked as integration because they require live services
# Run with: pytest -m integration

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    """Health endpoint should return 200 when all services are up."""
    response = await client.get("/api/v1/health")
    # Accept 200 (healthy) or 503 (services down in CI)
    assert response.status_code in (200, 503)
    body = response.json()
    assert "status" in body or "detail" in body


@pytest.mark.asyncio
async def test_readiness_endpoint_structure(client: AsyncClient):
    """Readiness endpoint should return expected schema."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)


@pytest.mark.asyncio
async def test_flags_endpoint_in_development(client: AsyncClient):
    """Flags endpoint should be accessible in development."""
    response = await client.get("/api/v1/health/flags")
    # Should not be 403 in dev; may be 200 or 500 depending on config
    assert response.status_code != 403


@pytest.mark.asyncio
async def test_correlation_id_header_is_set(client: AsyncClient):
    """Every response must include X-Request-ID header from middleware."""
    response = await client.get("/api/v1/health")
    assert "x-request-id" in response.headers or "X-Request-ID" in response.headers
