from __future__ import annotations

import asyncio
import structlog
from uuid import UUID

from app.services.chunk_storage import ChunkStorageService
from app.services.llm import LLMService
from app.utils.chunker import SemanticChunker

logger = structlog.get_logger(__name__)


class ChunkSummarizerPipeline:
    """Orchestrates token-safe, parallel semantic chunk summarization.

    1. Splits raw source document into semantic chunks using SemanticChunker.
    2. Caches raw chunks in Redis via ChunkStorageService.
    3. Runs high-concurrency parallel summarization on all chunks with rate-limit throttling.
    """

    def __init__(
        self,
        chunker: SemanticChunker | None = None,
        storage: ChunkStorageService | None = None,
        llm: LLMService | None = None,
        max_parallel_tasks: int = 5,
    ):
        self.chunker = chunker or SemanticChunker()
        self.storage = storage or ChunkStorageService()
        self.llm = llm or LLMService()
        self.semaphore = asyncio.Semaphore(max_parallel_tasks)

        logger.debug(
            "ChunkSummarizerPipeline initialized",
            max_parallel_tasks=max_parallel_tasks,
        )

    async def process_source(
        self,
        session_id: UUID,
        source_id: UUID,
        raw_text: str,
        title: str = "source document",
        max_chunk_tokens: int = 2000,
        chunk_overlap_tokens: int = 200,
    ) -> dict[str, any]:
        """Process a single large source text document, returning chunk summaries and metrics.

        Metrics returned:
            - chunk_count (int)
            - raw_token_count (int)
            - summary_token_count (int)
            - chunk_summaries (list[str])
        """
        if not raw_text or not raw_text.strip():
            return {
                "chunk_count": 0,
                "raw_token_count": 0,
                "summary_token_count": 0,
                "chunk_summaries": [],
            }

        # 1. Estimate raw tokens
        raw_token_count = self.chunker.estimator.estimate_tokens(raw_text)

        # 2. Slice text semantically
        chunks = self.chunker.split_text(
            text=raw_text,
            max_chunk_tokens=max_chunk_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
        )
        chunk_count = len(chunks)

        logger.info(
            "Split raw source into semantic chunks",
            source_id=str(source_id),
            raw_token_count=raw_token_count,
            chunk_count=chunk_count,
        )

        # 3. Store raw chunks in Redis cache (temporary/lightweight)
        await self.storage.store_chunks(session_id, source_id, chunks)

        # 4. Summarize all chunks concurrently (throttled by Semaphore)
        tasks = [
            self._summarize_single_chunk(
                chunk_text=chunk,
                chunk_index=i,
                total_chunks=chunk_count,
                title=title,
            )
            for i, chunk in enumerate(chunks)
        ]
        
        chunk_summaries = await asyncio.gather(*tasks)

        # 5. Calculate summary metrics
        full_summary_text = "\n\n".join(chunk_summaries)
        summary_token_count = self.chunker.estimator.estimate_tokens(full_summary_text)

        logger.info(
            "Completed parallel chunk summarization",
            source_id=str(source_id),
            chunk_count=chunk_count,
            summary_token_count=summary_token_count,
        )

        return {
            "chunk_count": chunk_count,
            "raw_token_count": raw_token_count,
            "summary_token_count": summary_token_count,
            "chunk_summaries": chunk_summaries,
        }

    async def _summarize_single_chunk(
        self, chunk_text: str, chunk_index: int, total_chunks: int, title: str
    ) -> str:
        """Throttled single chunk summarization task."""
        async with self.semaphore:
            context_hint = f"Part {chunk_index + 1} of {total_chunks} for '{title}'"
            logger.debug(
                "Summarizing individual source chunk",
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                text_len=len(chunk_text),
            )
            return await self.llm.summarize_text(chunk_text, context_hint=context_hint)
