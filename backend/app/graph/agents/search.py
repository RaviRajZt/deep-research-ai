# ============================================
# Deep Research Platform - Search Agent
# ============================================
"""
Search Agent for discovering and fetching relevant sources.

It receives the topic, uses a web search API (mocked for now), 
and stores the discovered sources in the Source repository.
It returns the IDs of the newly created sources to add to the state.
"""

from typing import Any, Dict
from app.graph.state import ResearchState
from app.graph.agents.base import BaseAgent
from app.repositories import SourceRepository
import uuid

class SearchAgent(BaseAgent):
    """
    Finds and fetches sources related to the topic.
    """

    def __init__(self, execution_log_repo: Any, session_repo: Any, source_repo: SourceRepository):
        super().__init__(name="search_agent", execution_log_repo=execution_log_repo, session_repo=session_repo)
        self.source_repo = source_repo

    async def __call__(self, state: ResearchState) -> Dict[str, Any]:
        """
        Execute the search and fetch step.
        """
        # Log step start
        log = await self.log_start(state, f"Searching for sources on topic: {state['topic']}")
        
        try:
            # 1. MOCK: Perform Search and get URLs
            # In a real implementation, this would call Tavily or Serper API
            mock_urls = [
                "https://example.com/article-1",
                "https://example.com/article-2",
            ]
            
            # 2. Bulk create sources in DB (status: pending)
            new_sources = await self.source_repo.bulk_create([
                {
                    "session_id": state["session_id"],
                    "url": url,
                    "fetch_status": "pending"
                }
                for url in mock_urls
            ])
            
            source_ids = [s.id for s in new_sources]
            
            # 3. MOCK: Fetch sources (would be a real fetcher here)
            for source in new_sources:
                await self.source_repo.update_fetch_status(
                    source_id=source.id,
                    fetch_status="fetched",
                    title="Mock Title",
                    content_hash=str(uuid.uuid4())[:8], # fake hash
                    raw_token_count=1000
                )
            
            # Log success
            await self.log_completion(log.id, f"Found and fetched {len(source_ids)} sources", {"source_ids": [str(sid) for sid in source_ids]})
            
            # Return new source IDs to be added to state (via operator.add)
            return {"source_ids": source_ids}
            
        except Exception as e:
            await self.log_failure(log.id, str(e))
            return {"errors": [f"SearchAgent failed: {str(e)}"]}
