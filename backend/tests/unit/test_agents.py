import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, ANY

from app.graph.agents.supervisor import SupervisorAgent
from app.graph.agents.search import SearchAgent
from app.graph.agents.summarizer import SummarizerAgent
from app.graph.agents.synthesizer import SynthesizerAgent
from app.core.enums import ResearchStatus

@pytest.fixture
def mock_exec_log_repo():
    repo = AsyncMock()
    repo.append_step.return_value = MagicMock(id=uuid.uuid4())
    repo.complete_step = AsyncMock()
    repo.fail_step = AsyncMock()
    return repo

@pytest.fixture
def mock_session_repo():
    repo = AsyncMock()
    repo.update_status = AsyncMock()
    repo.set_result = AsyncMock()
    return repo

@pytest.fixture
def mock_source_repo():
    repo = AsyncMock()
    repo.bulk_create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_session = AsyncMock()
    repo.update_fetch_status = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_supervisor_agent_routing(mock_exec_log_repo, mock_session_repo):
    """Test that SupervisorAgent routes correctly based on the ResearchState."""
    agent = SupervisorAgent(
        execution_log_repo=mock_exec_log_repo,
        session_repo=mock_session_repo
    )
    
    session_id = uuid.uuid4()
    
    # 1. If no source_ids, should route to search_agent
    state_1 = {"session_id": session_id, "source_ids": [], "summary_ids": [], "result_summary": None}
    res_1 = await agent(state_1)
    assert res_1["next_agent"] == "search_agent"
    mock_session_repo.update_status.assert_called_with(session_id, ResearchStatus.RESEARCHING)

    # 2. If source_ids populated but summary_ids incomplete, should route to summarizer_agent
    state_2 = {
        "session_id": session_id,
        "source_ids": [uuid.uuid4(), uuid.uuid4()],
        "summary_ids": [uuid.uuid4()],
        "result_summary": None
    }
    res_2 = await agent(state_2)
    assert res_2["next_agent"] == "summarizer_agent"
    mock_session_repo.update_status.assert_called_with(session_id, ResearchStatus.REVIEWING)

    # 3. If source_ids and summary_ids complete but result_summary empty, route to synthesizer_agent
    s_ids = [uuid.uuid4(), uuid.uuid4()]
    state_3 = {
        "session_id": session_id,
        "source_ids": s_ids,
        "summary_ids": s_ids,
        "result_summary": None
    }
    res_3 = await agent(state_3)
    assert res_3["next_agent"] == "synthesizer_agent"
    mock_session_repo.update_status.assert_called_with(session_id, ResearchStatus.WRITING)

    # 4. If all complete, should route to end
    state_4 = {
        "session_id": session_id,
        "source_ids": s_ids,
        "summary_ids": s_ids,
        "result_summary": "Done!"
    }
    res_4 = await agent(state_4)
    assert res_4["next_agent"] == "end"


@pytest.mark.asyncio
async def test_search_agent(mock_exec_log_repo, mock_session_repo, mock_source_repo):
    """Test that SearchAgent bulk creates sources and registers them in the database."""
    agent = SearchAgent(
        execution_log_repo=mock_exec_log_repo,
        session_repo=mock_session_repo,
        source_repo=mock_source_repo
    )
    
    session_id = uuid.uuid4()
    state = {
        "session_id": session_id,
        "topic": "test topic",
        "session_metadata": {"max_sources_target": 2}
    }
    
    mock_source = MagicMock()
    mock_source.id = uuid.uuid4()
    mock_source.url = "http://test.com"
    mock_source_repo.bulk_create.return_value = [mock_source]
    
    res = await agent(state)
    
    # Assert search bulk created sources and marked them as fetching
    mock_source_repo.bulk_create.assert_called_once()
    mock_source_repo.update_fetch_status.assert_called_once_with(
        source_id=mock_source.id,
        fetch_status="fetching",
        title="Discovered Source",
        content_hash=ANY,
        raw_token_count=100
    )
    
    # Assert returned state contains the populated source_ids
    assert mock_source.id in res["source_ids"]


@pytest.mark.asyncio
async def test_summarizer_agent(mock_exec_log_repo, mock_session_repo, mock_source_repo):
    """Test that SummarizerAgent splits raw webpage text, runs pipeline, and marks source as 'fetched'."""
    mock_pipeline = AsyncMock()
    mock_pipeline.process_source.return_value = {
        "chunk_count": 2,
        "raw_token_count": 500,
        "summary_token_count": 150,
        "chunk_summaries": ["Summary block 1", "Summary block 2"]
    }
    
    agent = SummarizerAgent(
        execution_log_repo=mock_exec_log_repo,
        session_repo=mock_session_repo,
        source_repo=mock_source_repo,
        pipeline=mock_pipeline
    )
    
    session_id = uuid.uuid4()
    source_id = uuid.uuid4()
    state = {
        "session_id": session_id,
        "topic": "test topic",
        "source_ids": [source_id]
    }
    
    mock_record = MagicMock()
    mock_record.title = "Test Webpage"
    mock_record.url = "http://example.com"
    mock_record.source_metadata = {}
    mock_source_repo.get_by_id.return_value = mock_record
    
    res = await agent(state)
    
    # Check that it processed through ChunkSummarizerPipeline
    mock_pipeline.process_source.assert_called_once()
    
    # Check that it updated the source repo with 'fetched' status, token counts, and summary text metadata
    mock_source_repo.update.assert_called_once_with(
        entity_id=source_id,
        fetch_status="fetched",
        raw_token_count=500,
        summary_token_count=150,
        chunk_count=2,
        source_metadata={"summary_text": "Summary block 1\n\nSummary block 2"}
    )
    
    # Check returned state contains the processed source in summary_ids
    assert source_id in res["summary_ids"]


@pytest.mark.asyncio
async def test_synthesizer_agent(mock_exec_log_repo, mock_session_repo, mock_source_repo):
    """Test that SynthesizerAgent aggregates summaries and compiles the final report."""
    mock_pipeline = AsyncMock()
    mock_pipeline.synthesize_article_summaries.return_value = "# Final Generated Research Report"
    mock_pipeline.estimator = MagicMock()
    mock_pipeline.estimator.estimate_tokens.return_value = 100
    
    agent = SynthesizerAgent(
        execution_log_repo=mock_exec_log_repo,
        session_repo=mock_session_repo,
        source_repo=mock_source_repo,
        pipeline=mock_pipeline
    )
    
    session_id = uuid.uuid4()
    state = {
        "session_id": session_id,
        "topic": "test topic",
    }
    
    mock_source = MagicMock()
    mock_source.source_metadata = {"summary_text": "Webpage Summary text"}
    mock_source_repo.get_by_session.return_value = [mock_source]
    
    res = await agent(state)
    
    # Check that it fetched successfully 'fetched' sources
    mock_source_repo.get_by_session.assert_called_once_with(session_id, fetch_status="fetched")
    
    # Check that it synthesized the report using ArticleSynthesisPipeline
    mock_pipeline.synthesize_article_summaries.assert_called_once_with(
        topic="test topic",
        chunk_summaries=["Webpage Summary text"],
        max_budget_tokens=100
    )
    
    # Check that it persisted the synthesized result to session repo
    mock_session_repo.set_result.assert_called_once_with(
        session_id=session_id,
        result_summary="# Final Generated Research Report",
        result_token_count=100
    )
    
    # Check that returned state contains the result summary
    assert res["result_summary"] == "# Final Generated Research Report"
