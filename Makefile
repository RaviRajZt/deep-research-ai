# ============================================
# Deep Research Platform - Makefile
# Developer ergonomics for common operations
# ============================================

.PHONY: help setup dev down build lint test clean migrate

# Default target
help: ## Show this help message
	@echo "Deep Research Platform - Development Commands"
	@echo "============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------- Setup ----------

setup: ## First-time project setup
	@echo "🔧 Setting up Deep Research Platform..."
	cp -n .env.example .env || true
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd frontend && npm install
	@echo "✅ Setup complete. Run 'make dev' to start."

# ---------- Development ----------

dev: ## Start all services for local development
	docker compose up -d postgres redis
	@echo "⏳ Waiting for services..."
	@sleep 3
	@echo "🚀 Starting backend and frontend..."
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Start backend dev server
	cd backend && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev

dev-docker: ## Start everything via Docker Compose
	docker compose up --build

# ---------- Infrastructure ----------

infra-up: ## Start infrastructure services (Postgres, Redis)
	docker compose up -d postgres redis

infra-down: ## Stop infrastructure services
	docker compose down

# ---------- Database ----------

migrate: ## Run database migrations
	cd backend && . .venv/bin/activate && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	cd backend && . .venv/bin/activate && alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	cd backend && . .venv/bin/activate && alembic downgrade -1

# ---------- Code Quality ----------

lint: ## Run all linters
	@echo "🔍 Linting backend..."
	cd backend && . .venv/bin/activate && ruff check . && mypy app/
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint

format: ## Format all code
	@echo "✨ Formatting backend..."
	cd backend && . .venv/bin/activate && ruff format .
	@echo "✨ Formatting frontend..."
	cd frontend && npm run format

# ---------- Testing ----------

test: ## Run all tests
	@echo "🧪 Testing backend..."
	cd backend && . .venv/bin/activate && pytest
	@echo "🧪 Testing frontend..."
	cd frontend && npm test

test-backend: ## Run backend tests only
	cd backend && . .venv/bin/activate && pytest -v

test-frontend: ## Run frontend tests only
	cd frontend && npm test

# ---------- Build ----------

build: ## Build production images
	docker compose -f docker-compose.prod.yml build

# ---------- Clean ----------

clean: ## Clean generated files and caches
	@echo "🧹 Cleaning..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next frontend/out
	@echo "✅ Clean complete."

down: ## Stop all Docker services and remove volumes
	docker compose down -v
