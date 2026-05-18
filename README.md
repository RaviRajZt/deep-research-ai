# Deep Research Platform

> **Enterprise AI Research Agent Platform**
> LangGraph + FastAPI + Next.js + Redis + PostgreSQL + SSE

## Architecture

This is a **modular monolith** following clean architecture principles:

```
deep-research/
├── backend/          # FastAPI async backend (Python 3.12+)
├── frontend/         # Next.js App Router (TypeScript)
├── shared/           # Cross-platform contracts & constants
├── infrastructure/   # Service configs (Nginx, Postgres, Redis)
├── scripts/          # Automation & CI/CD scripts
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Make (optional, for ergonomics)

### Setup

```bash
# 1. Clone and setup
make setup

# 2. Start infrastructure (Postgres + Redis)
make infra-up

# 3. Run database migrations
make migrate

# 4. Start development servers
make dev
```

Or with Docker Compose:

```bash
docker compose up --build
```

### Access Points

| Service    | URL                    |
|-----------|------------------------|
| Frontend  | http://localhost:3000   |
| Backend   | http://localhost:8000   |
| API Docs  | http://localhost:8000/docs |
| Health    | http://localhost:8000/api/v1/health |

## Development

```bash
make help        # Show all available commands
make dev         # Start all dev servers
make lint        # Run all linters
make format      # Format all code
make test        # Run all tests
make migrate     # Run database migrations
make clean       # Clean generated files
```

## Architecture Principles

- **Modular Monolith** — Feature-based modules with clear boundaries
- **Clean Architecture** — API → Service → Repository → Infrastructure
- **SOLID** — Single responsibility, dependency inversion via DI
- **Config-driven** — All behavior via environment + feature flags
- **Async-first** — All I/O uses async/await
- **Type-safe** — Pydantic v2 (backend), TypeScript strict (frontend)

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Supports three environments: `development`, `staging`, `production`

## Tech Stack

| Layer       | Technology                          |
|------------|-------------------------------------|
| Backend    | FastAPI, SQLAlchemy 2.x, Pydantic v2 |
| Frontend   | Next.js, TypeScript, TailwindCSS    |
| Database   | PostgreSQL 16+                      |
| Cache      | Redis 7+                            |
| Infra      | Docker, Docker Compose, Nginx       |
| Agents     | LangGraph (future phase)            |

## License

Proprietary — All rights reserved.
