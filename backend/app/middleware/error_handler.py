# ============================================
# Deep Research Platform - Error Handler Middleware
# ============================================
"""
Global exception handler that converts all application exceptions
into consistent JSON error responses.

WHY centralized error handling:
- Consistent error response format across all endpoints
- Prevents stack traces leaking to clients in production
- Structured error logging with context
- Maps custom exceptions to appropriate HTTP status codes
"""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.exceptions import AppException
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle all AppException subclasses with structured JSON responses.

    Response format:
    {
        "error": {
            "code": "NOT_FOUND",
            "message": "Resource not found",
            "details": { ... }
        }
    }
    """
    settings = get_settings()

    logger.warning(
        "Application exception",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": str(request.url),
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details if settings.is_development else {},
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors as 422 responses."""
    logger.debug("Validation error", extra={"errors": exc.errors()})
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.

    IMPORTANT: Never exposes internal details in production.
    Always logs the full traceback server-side.
    """
    settings = get_settings()

    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={"path": str(request.url), "method": request.method},
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                # Only expose details in development
                "details": {"type": type(exc).__name__} if settings.is_development else {},
            }
        },
    )
