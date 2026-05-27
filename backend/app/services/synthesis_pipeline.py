from __future__ import annotations

import asyncio
import structlog

from app.services.llm import LLMService
from app.utils.token import TokenEstimator

logger = structlog.get_logger(__name__)


class ArticleSynthesisPipeline:
    """Orchestrates token-safe hierarchical summary compression and grouped synthesis.

    Ensures that multiple chunk summaries are compacted recursively using a tree-like merge
    until they strictly fit within context budgets, then synthesizes them.
    """

    def __init__(
        self,
        token_estimator: TokenEstimator | None = None,
        llm: LLMService | None = None,
        max_parallel_tasks: int = 5,
    ):
        self.estimator = token_estimator or TokenEstimator()
        self.llm = llm or LLMService()
        self.semaphore = asyncio.Semaphore(max_parallel_tasks)

        logger.debug("ArticleSynthesisPipeline initialized")

    async def synthesize_article_summaries(
        self,
        topic: str,
        chunk_summaries: list[str],
        max_budget_tokens: int = 4000,
    ) -> str:
        """Compress chunk summaries hierarchically if they exceed budget, and synthesize them."""
        if not chunk_summaries:
            return "No content available to synthesize."

        # 1. Enforce hierarchical compression if summaries violate the budget
        compressed_summaries = await self.compress_hierarchically_if_needed(
            summaries=chunk_summaries,
            max_budget=max_budget_tokens,
            topic=topic,
        )

        # 2. Perform the final grouped synthesis on the safe summaries list
        logger.info(
            "Synthesizing final aggregated summaries",
            topic=topic,
            summaries_count=len(compressed_summaries),
        )
        return await self.llm.synthesize_summaries(topic, compressed_summaries)

    async def compress_hierarchically_if_needed(
        self,
        summaries: list[str],
        max_budget: int,
        topic: str,
        depth: int = 1,
    ) -> list[str]:
        """Recursively pairs and compresses adjacent summaries if their joint token count is over budget."""
        if not summaries:
            return []

        # Count total tokens of combined summaries
        joined_text = "\n\n".join(summaries)
        total_tokens = self.estimator.estimate_tokens(joined_text)

        if total_tokens <= max_budget or len(summaries) <= 1:
            logger.debug(
                "Summaries are within safe budget boundaries",
                total_tokens=total_tokens,
                max_budget=max_budget,
                summaries_count=len(summaries),
                depth=depth,
            )
            return summaries

        logger.info(
            "Summaries exceed budget. Triggering hierarchical compression step.",
            total_tokens=total_tokens,
            max_budget=max_budget,
            summaries_count=len(summaries),
            depth=depth,
        )

        # Pair adjacent summaries: group summaries in pairs of 2
        paired_groups: list[list[str]] = []
        for i in range(0, len(summaries), 2):
            group = summaries[i : i + 2]
            paired_groups.append(group)

        # Run parallel compression on paired groups
        tasks = [
            self._compress_single_group(group, topic, depth)
            for group in paired_groups
        ]
        
        compressed_groups = await asyncio.gather(*tasks)

        # Recurse if the resulting compressed list is still over the token budget
        return await self.compress_hierarchically_if_needed(
            summaries=compressed_groups,
            max_budget=max_budget,
            topic=topic,
            depth=depth + 1,
        )

    async def _compress_single_group(self, group: list[str], topic: str, depth: int) -> str:
        """Merge a group of 2 summaries into a single dense summary block."""
        async with self.semaphore:
            if len(group) == 1:
                return group[0]

            combined_text = "\n\n---\n\n".join(group)
            context_hint = f"Hierarchical compression depth {depth} for topic '{topic}'"
            logger.debug(
                "Compressing summary pair",
                group_len=len(group),
                depth=depth,
            )
            return await self.llm.summarize_text(combined_text, context_hint=context_hint)
