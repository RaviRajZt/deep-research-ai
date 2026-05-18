# ============================================
# Deep Research Platform - Structured Logging Setup
# ============================================
"""
Configures structlog for structured, JSON-based logging.

WHY structlog:
- JSON output in production for log aggregation (ELK, Datadog, etc.)
- Human-readable colored output in development
- Processor pipeline for enrichment (timestamp, level, correlation ID)
- Async-safe — no mutable shared state
- Compatible with stdlib logging for third-party library logs
"""

from __future__ import annotations

import logging
import sys

import structlog


def setup_logging(
    log_level: str = "INFO",
    environment: str = "development",
    app_name: str = "deep-research",
) -> None:
    """
    Bootstrap structured logging for the entire application.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Current environment — controls output format
        app_name: Application name injected into every log entry
    """
    # Shared processors applied to every log entry
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,      # Merge context vars (correlation ID)
        structlog.stdlib.add_log_level,                # Add log level
        structlog.stdlib.add_logger_name,              # Add logger name
        structlog.processors.TimeStamper(fmt="iso"),   # ISO8601 timestamp
        structlog.processors.StackInfoRenderer(),       # Stack info if present
        structlog.processors.UnicodeDecoder(),          # Decode bytes to str
    ]

    if environment == "development":
        # Human-readable, colored console output for development
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(
            colors=True,
        )
    else:
        # JSON output for production log aggregation
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog formatting
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Set root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Quiet noisy third-party loggers
    for noisy_logger in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Log startup confirmation
    logger = structlog.get_logger(app_name)
    logger.info(
        "Logging configured",
        log_level=log_level,
        environment=environment,
        format="json" if environment != "development" else "console",
    )
