# ============================================
# Deep Research Platform - Request Logging Middleware
# ============================================
"""
Structured HTTP request/response access logging.

Logs method, path, status code, and duration for every request.
Controlled by the ENABLE_REQUEST_LOGGING feature flag.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.feature_flags import FeatureFlag, feature_flags

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs HTTP access with timing information.

    Skips:
    - /api/v1/health endpoints (avoid log spam from probes)
    - Disabled when ENABLE_REQUEST_LOGGING feature flag is off

    Log fields: method, path, status_code, duration_ms
    """

    SKIP_PATHS = {"/api/v1/health", "/api/v1/ready", "/nginx-health"}

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Skip logging if flag is disabled
        if not feature_flags.is_enabled(FeatureFlag.ENABLE_REQUEST_LOGGING):
            return await call_next(request)

        # Skip health check paths to avoid log spam
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        log_method = logger.warning if response.status_code >= 500 else logger.info

        log_method(
            "HTTP request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_host": request.client.host if request.client else "unknown",
            },
        )

        # Inject timing header for debugging
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
