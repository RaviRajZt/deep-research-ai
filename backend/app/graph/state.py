# ============================================
# Deep Research Platform - LangGraph State
# ============================================
"""
Graph state architecture for the Research Multi-Agent workflow.

CRITICAL RULE: This state MUST remain lightweight and token-safe.
It should ONLY contain metadata, database IDs, and configuration.
It must NEVER store raw article content, large chunks, or uncompressed data.
All large content is passed by reference (database UUIDs) and fetched directly 
by the agents that need it.
"""

from typing import Annotated, TypedDict, Optional
import operator
import uuid


class ResearchState(TypedDict):
    """
    State object passed between LangGraph agents.
    
    Uses Annotated with operator.add for lists to automatically
    append items from agent outputs rather than overwriting.
    """
    
    # Core Session context
    session_id: uuid.UUID
    topic: str
    
    # Graph flow control
    current_step: str
    next_agent: str
    
    # Extracted data references
    # Instead of storing HTML, we store the DB UUIDs of the Source models
    source_ids: Annotated[list[uuid.UUID], operator.add]
    
    # Any intermediate summary references
    summary_ids: Annotated[list[uuid.UUID], operator.add]
    
    # Final generated summary text (this is the only large text stored, 
    # and it is heavily condensed by the synthesizer)
    result_summary: Optional[str]
    
    # Execution tracing and errors
    errors: Annotated[list[str], operator.add]
