# ============================================
# Deep Research Platform - FastAPI Application Factory
# ============================================
"""
Main application entry point.

WHY an app factory (create_app) instead of a module-level app:
- Enables testing with different configurations
- Cleaner separation of concerns
- Avoids circular imports during module loading
- Explicit dependency graph through function arguments
"""

from __future__ import annotations

from pydantic import ValidationError

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.core.constants import API_DESCRIPTION, API_TITLE, API_V1_PREFIX
from app.core.exceptions import AppException
from app.core.lifecycle import lifespan
from app.core.settings import get_settings
from app.middleware import (
    CorrelationIDMiddleware,
    RequestLoggingMiddleware,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


def create_app() -> FastAPI:
    """
    Application factory — creates and configures the FastAPI instance.

    Startup order:
    1. Load settings (fails fast on invalid config)
    2. Register lifespan (DB + Redis init/teardown)
    3. Register CORS middleware
    4. Register custom middleware stack
    5. Register exception handlers
    6. Mount API routers
    7. Return configured app
    """
    settings = get_settings()

    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=settings.__class__.__module__,  # resolved from pyproject
        lifespan=lifespan,
        # Disable docs in production for security
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    # ---------- CORS ----------
    # Must be registered BEFORE custom middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Correlation-ID", "X-Process-Time-Ms"],
    )

    # ---------- Custom Middleware (LIFO order) ----------
    # Starlette processes middleware in reverse registration order.
    # CorrelationIDMiddleware must run first (outermost) so that
    # RequestLoggingMiddleware can log the correlation ID.
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)

    # ---------- Exception Handlers ----------
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # ---------- Routers ----------
    app.include_router(api_v1_router, prefix=API_V1_PREFIX)

    return app


# Module-level app instance for uvicorn
app = create_app()
