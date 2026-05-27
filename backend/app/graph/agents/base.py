# ============================================
# Deep Research Platform - Base Agent
# ============================================
"""
Base classes for LangGraph agents.

WHY a BaseAgent:
- Ensures consistent dependency injection (DB sessions, repos)
- Standardizes ExecutionLog tracking across all agent steps
- Provides unified error handling and state updates
"""

from typing import Optional, Any
from app.graph.state import ResearchState
from app.repositories import ExecutionLogRepository, ResearchSessionRepository
from app.core.enums import ResearchStatus

class BaseAgent:
    """
    Base class for all orchestrator agents.
    Subclasses must implement the `__call__` or `run` method to conform 
    to the LangGraph node contract.
    """
    
    def __init__(self, name: str, execution_log_repo: ExecutionLogRepository, session_repo: Optional[ResearchSessionRepository] = None):
        """
        Args:
            name: Human-readable name of the agent (e.g. "search_agent", "supervisor")
            execution_log_repo: Repo to write step logs to the DB.
            session_repo: Optional repo to update overall session status.
        """
        self.name = name
        self.execution_log_repo = execution_log_repo
        self.session_repo = session_repo

    async def log_start(self, state: ResearchState, message: Optional[str] = None) -> Any:
        """
        Log the start of an agent's execution step.
        """
        return await self.execution_log_repo.append_step(
            session_id=state["session_id"],
            agent_role=self.name,
            step_name=self.name,
            status="running",
            message=message or f"Agent {self.name} started execution.",
        )

    async def log_completion(self, log_id: Any, message: Optional[str] = None, metadata: Optional[dict[str, Any]] = None) -> None:
        """
        Mark a step as completed.
        """
        await self.execution_log_repo.complete_step(
            log_id=log_id,
            message=message or f"Agent {self.name} completed successfully.",
            step_metadata=metadata
        )

    async def log_failure(self, log_id: Any, error: str) -> None:
        """
        Mark a step as failed.
        """
        await self.execution_log_repo.fail_step(
            log_id=log_id,
            error_detail=error
        )
