# ============================================
# Deep Research Platform - API v1 Router
# ============================================
"""
Central router that aggregates all v1 API sub-routers.

WHY aggregation pattern:
- Single mount point in main.py — clean app factory
- Easy to add new feature routers without touching main.py
- Enables per-feature middleware or dependencies at router level
- Version prefix managed here, not in individual routers
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router

# Future routers will be imported and included here:
# from app.api.v1.research import router as research_router

api_v1_router = APIRouter()

# Mount sub-routers
api_v1_router.include_router(health_router)

# Future:
# api_v1_router.include_router(research_router, prefix="/research")
# api_v1_router.include_router(agents_router, prefix="/agents")
