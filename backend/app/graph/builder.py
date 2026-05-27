# ============================================
# Deep Research Platform - Graph Builder
# ============================================
"""
Constructs the LangGraph workflow.
"""

from langgraph.graph import StateGraph, END
from app.graph.state import ResearchState
from app.graph.agents.supervisor import SupervisorAgent
from app.graph.agents.search import SearchAgent
from app.graph.agents.summarizer import SummarizerAgent
from app.graph.agents.synthesizer import SynthesizerAgent

def build_research_graph(
    execution_log_repo, 
    session_repo, 
    source_repo
):
    """
    Builds and returns the compiled LangGraph.
    """
    # Initialize agents
    supervisor = SupervisorAgent(execution_log_repo, session_repo)
    search_agent = SearchAgent(execution_log_repo, session_repo, source_repo)
    summarizer_agent = SummarizerAgent(execution_log_repo, session_repo, source_repo)
    synthesizer_agent = SynthesizerAgent(execution_log_repo, session_repo, source_repo)

    # Initialize graph
    builder = StateGraph(ResearchState)

    # Add nodes
    builder.add_node("supervisor", supervisor)
    builder.add_node("search_agent", search_agent)
    builder.add_node("summarizer_agent", summarizer_agent)
    builder.add_node("synthesizer_agent", synthesizer_agent)

    # Add edges
    # The supervisor is the entry point
    builder.set_entry_point("supervisor")

    # Conditional routing from supervisor
    builder.add_conditional_edges(
        "supervisor",
        # The routing function just reads the next_agent from state
        lambda state: state.get("next_agent", "end"),
        {
            "search_agent": "search_agent",
            "summarizer_agent": "summarizer_agent",
            "synthesizer_agent": "synthesizer_agent",
            "end": END
        }
    )

    # After any worker agent finishes, it routes back to the supervisor
    builder.add_edge("search_agent", "supervisor")
    builder.add_edge("summarizer_agent", "supervisor")
    builder.add_edge("synthesizer_agent", "supervisor")

    return builder.compile()
