from __future__ import annotations

import asyncio
import structlog
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session, get_session_factory
from app.core.settings import get_settings
from app.core.enums import ResearchStatus
from app.schemas.research import ResearchSessionCreate, ResearchSessionResponse, ResearchSessionListResponse, SourceResponse
from app.repositories import ResearchSessionRepository, ExecutionLogRepository, SourceRepository
from app.graph.builder import build_research_graph
from app.services.stream import StreamService

logger = structlog.get_logger(__name__)

router = APIRouter()


async def run_research_workflow(session_id: UUID, topic: str) -> None:
    """Executes the multi-agent LangGraph workflow inside a background thread with an isolated DB session.

    Ensures step transitions are fully committed immediately to bubble up to SSE subscribers.
    """
    logger.info("Initializing background research workflow task", session_id=str(session_id), topic=topic)
    
    settings = get_settings()
    factory = get_session_factory(settings)
    
    # 1. Open isolated DB session
    async with factory() as db:
        try:
            # Instantiate isolated repositories
            execution_log_repo = ExecutionLogRepository(db)
            session_repo = ResearchSessionRepository(db)
            source_repo = SourceRepository(db)
            
            # 2. Advance session to planning phase
            await session_repo.update_status(session_id, ResearchStatus.PLANNING)
            await db.commit()
            
            # 3. Build multi-agent graph
            graph = build_research_graph(
                execution_log_repo=execution_log_repo,
                session_repo=session_repo,
                source_repo=source_repo
            )
            
            initial_state = {
                "session_id": session_id,
                "topic": topic,
                "current_step": "init",
                "next_agent": "",
                "source_ids": [],
                "summary_ids": [],
                "errors": [],
                "result_summary": None,
            }
            
            # 4. Stream step-by-step agent execution
            async for output in graph.astream(initial_state):
                logger.debug("Graph step execution checkpoint", session_id=str(session_id), node=output)
                # Commit updates immediately to push states through Redis Pub/Sub
                await db.commit()
                
            logger.info("Background research workflow completed successfully", session_id=str(session_id))
            
        except Exception as e:
            logger.exception("Background research graph execution crashed", session_id=str(session_id))
            # Safely log failure to the database session
            try:
                async with factory() as error_db:
                    error_session_repo = ResearchSessionRepository(error_db)
                    await error_session_repo.update_status(
                        session_id=session_id,
                        status=ResearchStatus.FAILED,
                        error_message=f"Agent workflow error: {str(e)}",
                    )
                    await error_db.commit()
            except Exception as db_err:
                logger.error("Failed to persist execution error state to DB", error=str(db_err))


# ------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------

@router.post(
    "/session",
    response_model=ResearchSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start a new research session",
)
async def create_research_session(
    payload: ResearchSessionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> ResearchSessionResponse:
    """Create a new research session and initiate background agent execution."""
    session_repo = ResearchSessionRepository(db)
    
    # 1. Persist the session to the DB
    session = await session_repo.create(
        topic=payload.topic,
        status=ResearchStatus.PENDING,
        session_metadata=payload.session_metadata,
    )
    
    # Commit immediately to get the ID and setup records
    await db.commit()
    
    # 2. Delegate the graph pipeline execution to a safe background task
    background_tasks.add_task(run_research_workflow, session.id, payload.topic)
    
    return ResearchSessionResponse.model_validate(session)


@router.get(
    "/stream/{session_id}",
    response_class=StreamingResponse,
    summary="Subscribe to a session's real-time progress update SSE stream",
)
async def stream_session_events(
    session_id: UUID,
) -> StreamingResponse:
    """Provides a Server-Sent Events (SSE) stream pushing updates from the agent execution workflow."""
    stream_service = StreamService()
    
    # We yield the stream generator directly into a StreamingResponse with SSE headers
    return StreamingResponse(
        stream_service.subscribe_session(session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Prevents Nginx/proxy buffer latency on stream events
        },
    )


@router.get(
    "/session/{session_id}",
    response_model=ResearchSessionResponse,
    summary="Get detailed status and statistics of a research session",
)
async def get_session_details(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ResearchSessionResponse:
    """Get the full record of a research session, including statuses and reports."""
    session_repo = ResearchSessionRepository(db)
    session = await session_repo.get_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session with ID {session_id} not found",
        )
    return ResearchSessionResponse.model_validate(session)


@router.get(
    "/session/{session_id}/logs",
    summary="Get the historical audit log/timeline for a research session",
)
async def get_session_timeline(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Retrieve all execution steps recorded for this research session."""
    log_repo = ExecutionLogRepository(db)
    logs = await log_repo.get_by_session(session_id)
    return [
        {
            "id": str(log.id),
            "agent_role": log.agent_role,
            "step_name": log.step_name,
            "status": log.status,
            "message": log.message,
            "duration_ms": log.duration_ms,
            "token_count": log.token_count,
            "step_order": log.step_order,
            "step_metadata": log.step_metadata,
            "error_detail": log.error_detail,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get(
    "/session",
    response_model=ResearchSessionListResponse,
    summary="List historical research sessions with pagination",
)
async def list_research_sessions(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
) -> ResearchSessionListResponse:
    """Fetch paginated summary of all historical research sessions."""
    session_repo = ResearchSessionRepository(db)
    
    # Fetch list
    sessions = await session_repo.get_all(limit=limit, offset=offset)
    
    # Fetch total count
    total = len(await session_repo.get_all(limit=100000))
    
    return ResearchSessionListResponse(
        items=[ResearchSessionResponse.model_validate(s) for s in sessions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/session/{session_id}/sources",
    response_model=list[SourceResponse],
    summary="Get all web sources fetched for a research session",
)
async def get_session_sources(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[SourceResponse]:
    """Retrieve all web sources discovered and fetched for this research session."""
    source_repo = SourceRepository(db)
    sources = await source_repo.get_by_session(session_id)
    return [SourceResponse.model_validate(source) for source in sources]
