# ============================================
# Deep Research Platform - Supervisor Agent
# ============================================
"""
Supervisor Agent for orchestrating the LangGraph workflow.

The supervisor's job is purely to determine routing logic:
- Which agent should run next?
- Is the research complete?
- Should we fail early?

It evaluates the state and returns the updated `next_agent`.
"""

from typing import Any, Dict
from app.graph.state import ResearchState
from app.graph.agents.base import BaseAgent
from app.core.enums import ResearchStatus

class SupervisorAgent(BaseAgent):
    """
    Evaluates current state and conditionally routes to the next agent.
    """

    def __init__(self, execution_log_repo: Any, session_repo: Any):
        super().__init__(name="supervisor", execution_log_repo=execution_log_repo, session_repo=session_repo)

    async def __call__(self, state: ResearchState) -> Dict[str, Any]:
        """
        Evaluate state and return the next agent.
        """
        # Log step start
        log = await self.log_start(state, "Supervisor evaluating next steps")
        
        # Simple finite state machine logic based on populated IDs
        next_agent = "end"
        
        if not state.get("source_ids"):
            # If no sources fetched yet, go to search
            next_agent = "search_agent"
            message = "Routing to search_agent"
        elif not state.get("summary_ids") or len(state["summary_ids"]) < len(state["source_ids"]):
            # If not all sources have summaries, go to summarizer
            next_agent = "summarizer_agent"
            message = "Routing to summarizer_agent"
        elif not state.get("result_summary"):
            # If we have summaries but no final result, go to synthesizer
            next_agent = "synthesizer_agent"
            message = "Routing to synthesizer_agent"
        else:
            # Everything is done
            next_agent = "end"
            message = "Research complete. Routing to END."

        # Update the session status based on next step
        if self.session_repo and next_agent != "end":
            status_map = {
                "search_agent": ResearchStatus.RESEARCHING,
                "summarizer_agent": ResearchStatus.REVIEWING,
                "synthesizer_agent": ResearchStatus.WRITING,
            }
            if next_agent in status_map:
                await self.session_repo.update_status(state["session_id"], status_map[next_agent])

        # Complete step log
        await self.log_completion(log.id, message, {"next_agent": next_agent})
        
        # Return partial state update
        return {"next_agent": next_agent}
