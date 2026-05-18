# ============================================
# Deep Research Platform - Exception Hierarchy
# ============================================
# Structured exception classes for consistent error handling.
#
# WHY a custom exception hierarchy:
# - Maps cleanly to HTTP status codes
# - Carries structured error context
# - Enables centralized error handling in middleware
# - Prevents leaking internal errors to clients
# - Supports error classification for logging/metrics
# ============================================

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """
    Base exception for all application errors.

    All custom exceptions inherit from this so middleware can
    catch `AppException` and handle them uniformly.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


# ---------- Client Errors (4xx) ----------


class BadRequestException(AppException):
    """400 — Request is malformed or invalid."""

    def __init__(
        self,
        message: str = "Bad request",
        *,
        error_code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message, status_code=400, error_code=error_code, details=details
        )


class UnauthorizedException(AppException):
    """401 — Authentication required or failed."""

    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        error_code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message, status_code=401, error_code=error_code, details=details
        )


class ForbiddenException(AppException):
    """403 — Authenticated but insufficient permissions."""

    def __init__(
        self,
        message: str = "Forbidden",
        *,
        error_code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message, status_code=403, error_code=error_code, details=details
        )


class NotFoundException(AppException):
    """404 — Requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        *,
        resource_type: str = "Resource",
        resource_id: str | None = None,
        error_code: str = "NOT_FOUND",
    ) -> None:
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(
            message, status_code=404, error_code=error_code, details=details
        )


class ConflictException(AppException):
    """409 — Resource state conflict (e.g., duplicate creation)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        *,
        error_code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message, status_code=409, error_code=error_code, details=details
        )


class RateLimitedException(AppException):
    """429 — Too many requests."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int = 60,
    ) -> None:
        super().__init__(
            message,
            status_code=429,
            error_code="RATE_LIMITED",
            details={"retry_after": retry_after},
        )


class UnprocessableException(AppException):
    """422 — Request understood but cannot be processed."""

    def __init__(
        self,
        message: str = "Unprocessable entity",
        *,
        error_code: str = "UNPROCESSABLE_ENTITY",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message, status_code=422, error_code=error_code, details=details
        )


# ---------- Server Errors (5xx) ----------


class InternalException(AppException):
    """500 — Unexpected internal server error."""

    def __init__(
        self,
        message: str = "Internal server error",
        *,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message, status_code=500, error_code=error_code, details=details
        )


class ServiceUnavailableException(AppException):
    """503 — Downstream service unavailable."""

    def __init__(
        self,
        message: str = "Service unavailable",
        *,
        service: str = "unknown",
    ) -> None:
        super().__init__(
            message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service},
        )


class ExternalServiceException(AppException):
    """502 — External API call failed."""

    def __init__(
        self,
        message: str = "External service error",
        *,
        service: str = "unknown",
        error_code: str = "EXTERNAL_SERVICE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        _details = {"service": service, **(details or {})}
        super().__init__(
            message, status_code=502, error_code=error_code, details=_details
        )
