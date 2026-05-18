#!/usr/bin/env bash
# ============================================
# Deep Research Platform - Health Check Script
# ============================================
# Verifies all services are reachable.
# Usage: bash scripts/health-check.sh
# ============================================

set -euo pipefail

API_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

ok()   { echo -e "\033[0;32m[✓]\033[0m $1"; }
fail() { echo -e "\033[0;31m[✗]\033[0m $1"; }

echo "Checking platform health..."
echo ""

# Backend health
if curl -sf "${API_URL}/api/v1/health" -o /dev/null; then
  ok "Backend API reachable at ${API_URL}"
else
  fail "Backend API NOT reachable at ${API_URL}"
fi

# Backend readiness
READY=$(curl -sf "${API_URL}/api/v1/health/ready" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ready', False))" 2>/dev/null || echo "false")
if [ "$READY" = "True" ]; then
  ok "Backend readiness: READY"
else
  fail "Backend readiness: NOT READY"
fi

# Frontend
if curl -sf "${FRONTEND_URL}" -o /dev/null; then
  ok "Frontend reachable at ${FRONTEND_URL}"
else
  fail "Frontend NOT reachable at ${FRONTEND_URL}"
fi

echo ""
