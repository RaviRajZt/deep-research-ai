from __future__ import annotations

import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.settings import get_settings
from app.redis_.client import init_redis, close_redis


from app.db.session import dispose_engine


@pytest_asyncio.fixture(autouse=True)
async def redis_setup():
    """Ensure Redis is initialized before running each test and closed after."""
    settings = get_settings()
    await init_redis(settings)
    yield
    await close_redis()


@pytest_asyncio.fixture(autouse=True)
async def db_setup():
    """Ensure database connection pool is fresh and bound to the current test event loop."""
    await dispose_engine()
    yield
    await dispose_engine()


@pytest.mark.asyncio
async def test_create_session_endpoint(client: AsyncClient) -> None:
    """POST /session should create a research session and trigger background tasks."""
    payload = {
        "topic": "Telecom Infrastructure Optimization",
        "session_metadata": {"concurrency_limit": 3},
    }
    response = await client.post("/api/v1/research/session", json=payload)
    assert response.status_code == 201
    
    body = response.json()
    assert "id" in body
    assert body["topic"] == payload["topic"]
    assert body["status"] == "pending"
    assert body["session_metadata"] == payload["session_metadata"]


@pytest.mark.asyncio
async def test_get_session_details_endpoint(client: AsyncClient) -> None:
    """GET /session/{session_id} should return session telemetry details."""
    # 1. Create a session
    payload = {"topic": "Biomedical Telemetry Patterns"}
    create_res = await client.post("/api/v1/research/session", json=payload)
    session_id = create_res.json()["id"]

    # 2. Get details
    response = await client.get(f"/api/v1/research/session/{session_id}")
    assert response.status_code == 200
    
    body = response.json()
    assert body["id"] == session_id
    assert body["topic"] == payload["topic"]


@pytest.mark.asyncio
async def test_stream_session_events_endpoint(client: AsyncClient) -> None:
    """GET /stream/{session_id} should yield the connection confirmation event immediately."""
    session_id = uuid.uuid4()

    # Invoke stream endpoint directly to bypass Starlette middleware buffering test bugs
    from app.api.v1.research import stream_session_events
    response = await stream_session_events(session_id)
    assert response.media_type == "text/event-stream"
    
    # Read the first event from the body iterator
    event_lines = []
    async for event in response.body_iterator:
        event_lines.append(event)
        break
        
    full_event = "\n".join(event_lines)
    assert "event: connected" in full_event
    assert "subscribed" in full_event


@pytest.mark.asyncio
async def test_get_timeline_logs_endpoint(client: AsyncClient) -> None:
    """GET /session/{session_id}/logs should return the timeline array."""
    # 1. Create a session
    payload = {"topic": "Dynamic Scaling Protocols"}
    create_res = await client.post("/api/v1/research/session", json=payload)
    session_id = create_res.json()["id"]

    # Let the background task append initial steps
    await asyncio.sleep(0.5)

    # 2. Query timeline logs
    response = await client.get(f"/api/v1/research/session/{session_id}/logs")
    assert response.status_code == 200
    
    body = response.json()
    assert isinstance(body, list)
    # Check that any generated steps conform to the expected log contract
    for log in body:
        assert "id" in log
        assert "agent_role" in log
        assert "step_name" in log
        assert "status" in log


@pytest.mark.asyncio
async def test_list_sessions_endpoint(client: AsyncClient) -> None:
    """GET /session should return paginated list of sessions."""
    response = await client.get("/api/v1/research/session?limit=5")
    assert response.status_code == 200
    
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert "limit" in body
    assert "offset" in body
    assert len(body["items"]) <= 5
