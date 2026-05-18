# ============================================
# Deep Research Platform - Backend Dockerfile (Production)
# ============================================
# Multi-stage build for minimal production image.
# Stage 1: Install dependencies
# Stage 2: Copy app code into clean runtime image
# ============================================

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies needed for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency specification first (layer caching)
COPY pyproject.toml ./

# Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY ./app ./app
COPY ./alembic.ini ./alembic.ini
COPY ./alembic ./alembic

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')" || exit 1

# Expose port
EXPOSE 8000

# Run with uvicorn (production settings)
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--no-access-log"]
