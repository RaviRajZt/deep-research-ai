# ============================================
# Deep Research Platform - Test Configuration
# ============================================
"""
Pytest fixtures and configuration for the backend test suite.

Test architecture:
- Unit tests: no external services (mock DB/Redis)
- Integration tests: real Postgres + Redis (use pytest marks)
- Async test support via pytest-asyncio

WHY AsyncClient for integration tests:
- Tests the full ASGI stack including middleware
- Identical to real HTTP requests
- No mocking required for contract tests
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

from app.main import app


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the async backend for pytest-asyncio."""
    return "asyncio"


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """
    Provides an async HTTP test client for endpoint testing.

    Uses ASGITransport to call the ASGI app directly without
    starting a real HTTP server.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
