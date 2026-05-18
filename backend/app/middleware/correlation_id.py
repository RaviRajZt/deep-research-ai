# ============================================
# Deep Research Platform - Correlation ID Middleware
# ============================================
"""
Injects a unique request correlation ID into every request context.

WHY correlation IDs:
- Trace a single request across logs, services, and async tasks
- Enables log aggregation filtering (grep by X-Request-ID)
- Required for distributed tracing (future Jaeger/OTEL integration)
- Propagated in response headers so clients can reference it
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.constants import HEADER_CORRELATION_ID, HEADER_REQUEST_ID


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates or propagates a correlation ID per request.

    Priority:
    1. Use existing X-Correlation-ID from incoming request headers (upstream proxy)
    2. Use existing X-Request-ID from incoming headers
    3. Generate a new UUID v4

    The ID is:
    - Bound to structlog's context vars (appears in ALL log entries for this request)
    - Added to the response headers so clients can reference it
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Resolve correlation ID with priority chain
        correlation_id = (
            request.headers.get(HEADER_CORRELATION_ID)
            or request.headers.get(HEADER_REQUEST_ID)
            or str(uuid.uuid4())
        )

        # Bind to structlog context — flows into all log entries for this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        # Propagate ID in response headers
        response.headers[HEADER_REQUEST_ID] = correlation_id
        response.headers[HEADER_CORRELATION_ID] = correlation_id

        return response

