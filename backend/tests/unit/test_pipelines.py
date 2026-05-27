from __future__ import annotations

import uuid
import pytest
import pytest_asyncio

from app.core.settings import get_settings
from app.redis_.client import close_redis, init_redis
from app.services.chunk_storage import ChunkStorageService
from app.services.summarizer_pipeline import ChunkSummarizerPipeline
from app.services.synthesis_pipeline import ArticleSynthesisPipeline


@pytest_asyncio.fixture(autouse=True)
async def redis_setup():
    """Ensure Redis is initialized before running each test and closed after."""
    settings = get_settings()
    await init_redis(settings)
    yield
    await close_redis()


@pytest_asyncio.fixture
def storage_service() -> ChunkStorageService:
    return ChunkStorageService()


@pytest_asyncio.fixture
def summarizer_pipeline() -> ChunkSummarizerPipeline:
    return ChunkSummarizerPipeline(max_parallel_tasks=3)


@pytest_asyncio.fixture
def synthesis_pipeline() -> ArticleSynthesisPipeline:
    return ArticleSynthesisPipeline(max_parallel_tasks=3)


@pytest.mark.asyncio
async def test_chunk_storage_operations(storage_service: ChunkStorageService) -> None:
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()
    mock_chunks = [
        "This is chunk number one of the document content.",
        "Here resides the second chunk, explaining the baseline data.",
        "Finally, this third chunk provides a concluding summary.",
    ]

    # 1. Store chunks
    stored = await storage_service.store_chunks(session_id, source_id, mock_chunks, ttl=100)
    assert stored is True

    # 2. Retrieve chunks
    retrieved = await storage_service.get_chunks(session_id, source_id)
    assert retrieved == mock_chunks

    # 3. Delete chunks
    deleted = await storage_service.delete_chunks(session_id, source_id)
    assert deleted is True

    # 4. Check cache miss
    miss = await storage_service.get_chunks(session_id, source_id)
    assert miss is None


@pytest.mark.asyncio
async def test_chunk_summarizer_pipeline_e2e(
    summarizer_pipeline: ChunkSummarizerPipeline,
) -> None:
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()

    # Large text with natural paragraph separations to trigger multiple splits
    large_text = (
        "Paragraph One of our text segment. It contains essential domain elements.\n\n"
        "Paragraph Two detailing high-concurrency systems, and Redis databases.\n\n"
        "Paragraph Three concluding that multi-agent orchestration performs well."
    )

    # Force low chunk sizes to trigger splits
    result = await summarizer_pipeline.process_source(
        session_id=session_id,
        source_id=source_id,
        raw_text=large_text,
        title="Telemetry Report",
        max_chunk_tokens=15,
        chunk_overlap_tokens=0,
    )

    # Assert outputs and metrics
    assert result["chunk_count"] >= 3
    assert result["raw_token_count"] > 0
    assert result["summary_token_count"] > 0
    assert len(result["chunk_summaries"]) == result["chunk_count"]

    # Verify that raw chunks were stored in Redis cache during process
    cached_chunks = await summarizer_pipeline.storage.get_chunks(session_id, source_id)
    assert cached_chunks is not None
    assert len(cached_chunks) == result["chunk_count"]

    # Cleanup cache
    await summarizer_pipeline.storage.delete_chunks(session_id, source_id)


@pytest.mark.asyncio
async def test_article_synthesis_pipeline_budget_compression(
    synthesis_pipeline: ArticleSynthesisPipeline,
) -> None:
    topic = "Quantum Telemetry"
    mock_summaries = [
        "First summary outlining hardware calibration parameters.",
        "Second summary describing data collection protocols.",
        "Third summary establishing network routing structures.",
        "Fourth summary outlining final system analysis.",
    ]

    # Estimate total token count to set budget
    full_text = "\n\n".join(mock_summaries)
    total_tokens = synthesis_pipeline.estimator.estimate_tokens(full_text)

    # Set budget lower than total token size to trigger hierarchical compression
    max_budget = total_tokens - 10
    
    synthesis = await synthesis_pipeline.synthesize_article_summaries(
        topic=topic,
        chunk_summaries=mock_summaries,
        max_budget_tokens=max_budget,
    )

    # Check that synthesis generated valid results
    assert " Quantum Telemetry" in synthesis or "Telemetry" in synthesis
    assert len(synthesis) > 0
