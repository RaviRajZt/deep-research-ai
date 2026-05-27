from __future__ import annotations

import structlog
from typing import Any, Dict
from app.graph.state import ResearchState
from app.graph.agents.base import BaseAgent
from app.repositories import ResearchSessionRepository, SourceRepository
from app.services.synthesis_pipeline import ArticleSynthesisPipeline

logger = structlog.get_logger(__name__)


class SynthesizerAgent(BaseAgent):
    """Synthesizes the final research report from individual source summaries.

    Uses ArticleSynthesisPipeline to enforce token budgets and run hierarchical merges.
    """

    def __init__(
        self,
        execution_log_repo: Any,
        session_repo: ResearchSessionRepository,
        source_repo: SourceRepository | None = None,
        pipeline: ArticleSynthesisPipeline | None = None,
    ):
        super().__init__(
            name="synthesizer_agent",
            execution_log_repo=execution_log_repo,
            session_repo=session_repo,
        )
        self.source_repo = source_repo
        self.pipeline = pipeline or ArticleSynthesisPipeline()

    async def __call__(self, state: ResearchState) -> Dict[str, Any]:
        """Execute the hierarchical synthesis step."""
        log = await self.log_start(state, "Synthesizing final research report with token-safe pipelines")
        
        try:
            session_id = state["session_id"]
            topic = state.get("topic", "general research")

            if not self.source_repo:
                raise RuntimeError("SourceRepository not injected into SynthesizerAgent.")

            # 1. Fetch all successfully fetched sources for this session
            sources = await self.source_repo.get_by_session(session_id, fetch_status="fetched")
            
            # 2. Extract their summarized text strings from metadata
            summaries: list[str] = []
            for source in sources:
                meta = source.source_metadata or {}
                summary_text = meta.get("summary_text")
                if summary_text:
                    summaries.append(summary_text)

            logger.info(
                "SynthesizerAgent aggregating summaries",
                session_id=str(session_id),
                sources_count=len(sources),
                summaries_count=len(summaries),
            )

            # 3. Compile and compress summaries through the ArticleSynthesisPipeline
            final_report = await self.pipeline.synthesize_article_summaries(
                topic=topic,
                chunk_summaries=summaries,
                max_budget_tokens=100,  # Target a low budget for testing hierarchical compression in integration tests
            )

            # Calculate report token size
            result_token_count = self.pipeline.estimator.estimate_tokens(final_report)

            # 4. Persist result report to PostgreSQL
            if self.session_repo:
                await self.session_repo.set_result(
                    session_id=session_id,
                    result_summary=final_report,
                    result_token_count=result_token_count,
                )
            
            await self.log_completion(
                log_id=log.id,
                message="Synthesis complete",
                metadata={"result_token_count": result_token_count},
            )
            
            # Return the final result to state
            return {"result_summary": final_report}
            
        except Exception as e:
            logger.error("SynthesizerAgent failed execution", error=str(e))
            await self.log_failure(log.id, str(e))
            return {"errors": [f"SynthesizerAgent failed: {str(e)}"]}
