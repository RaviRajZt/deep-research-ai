# ============================================
# Deep Research Platform - Models Package
# ============================================
# IMPORTANT: All models must be imported here so that Alembic's
# autogenerate can detect table changes via Base.metadata.
#
# Alembic env.py imports this module before running migrations.
# If a model is not imported here, its table won't be managed.
# ============================================

from app.models.audit_log import AuditLog
from app.models.execution_log import ExecutionLog
from app.models.research_session import ResearchSession
from app.models.source import Source

__all__ = [
    "AuditLog",
    "ExecutionLog",
    "ResearchSession",
    "Source",
]
