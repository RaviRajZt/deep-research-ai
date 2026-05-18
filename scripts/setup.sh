#!/usr/bin/env bash
# ============================================
# Deep Research Platform - Development Setup Script
# ============================================
# Run once after cloning the repository.
# Usage: bash scripts/setup.sh
# ============================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

log()  { echo -e "${CYAN}[setup]${RESET} $1"; }
ok()   { echo -e "${GREEN}[✓]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }

echo -e "\n${BOLD}Deep Research Platform — Development Setup${RESET}\n"

# ---------- Prerequisites ----------
log "Checking prerequisites..."

command -v python3 >/dev/null || { echo "❌ python3 not found"; exit 1; }
command -v node    >/dev/null || { echo "❌ node not found"; exit 1; }
command -v docker  >/dev/null || { echo "❌ docker not found"; exit 1; }
ok "All prerequisites found"

# ---------- Root .env ----------
if [ ! -f ".env" ]; then
  cp .env.example .env
  ok "Created .env from .env.example"
else
  warn ".env already exists — skipping"
fi

# ---------- Frontend .env.local ----------
if [ ! -f "frontend/.env.local" ]; then
  cp frontend/.env.local.example frontend/.env.local
  ok "Created frontend/.env.local"
else
  warn "frontend/.env.local already exists — skipping"
fi

# ---------- Backend Python venv ----------
log "Setting up backend Python virtual environment..."
cd backend
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  ok "Created .venv"
fi
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -e ".[dev]"
ok "Backend dependencies installed"
cd ..

# ---------- Frontend Node modules ----------
log "Installing frontend Node.js dependencies..."
cd frontend
npm install --silent
ok "Frontend dependencies installed"
cd ..

# ---------- Infrastructure ----------
log "Starting Docker infrastructure (Postgres + Redis)..."
docker compose up -d postgres redis
ok "Docker services started"

echo ""
echo -e "${BOLD}${GREEN}✅ Setup complete!${RESET}"
echo ""
echo "Next steps:"
echo "  1. Run migrations:  make migrate"
echo "  2. Start dev:       make dev"
echo "  3. Open browser:    http://localhost:3000"
echo "  4. API docs:        http://localhost:8000/docs"
echo ""
