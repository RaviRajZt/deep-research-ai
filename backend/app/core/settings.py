# ============================================
# Deep Research Platform - Settings Re-export
# ============================================
# This module exists for clean import ergonomics:
#   from app.core.settings import get_settings
# ============================================

from app.core import AppSettings, get_settings

__all__ = ["AppSettings", "get_settings"]
