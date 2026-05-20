# Anti-Gravity AI Research Platform - Project Details

## 1. Project Overview
A production-grade, distributed AI research orchestration platform that uses a Multi-Source Research Agent Platform with a Real-Time Streaming UI.
Users enter a research topic, and the backend orchestrates multiple AI specialist agents using LangGraph (Supervisor, Search, Summarizer, Synthesizer). The system streams live progress updates to the frontend using FastAPI SSE. 

## 2. Technology Stack
**Frontend:**
- Next.js (App Router)
- TypeScript
- Tailwind CSS
- EventSource (SSE)
- Zustand (scalable state management)

**Backend:**
- FastAPI (Async-first)
- LangGraph (Agent Orchestration)
- AsyncIO
- Pydantic
- SQLAlchemy & Alembic (Migrations)

**Infrastructure:**
- Redis (Caching, Streaming State, Intermediate Memory)
- PostgreSQL (Persistent History, Logs, Sessions)
- Docker & Docker Compose

## 3. Core System Flow
1. User submits a research topic.
2. Supervisor agent orchestrates the workflow.
3. Search agent finds relevant sources.
4. Extractor pipeline fetches content.
5. Content is chunked into manageable pieces.
6. Chunk summaries are generated.
7. Article summaries are generated.
8. Grouped synthesis is generated.
9. Final report is synthesized.
10. Major steps stream progress updates via SSE.
11. Frontend updates the UI in real time.

## 4. LLM & Token Safety Requirements
**Primary LLM:** Gemma 4 E4B Open Source Model (128K context window).
Despite the large context window, the architecture **MUST** prevent context explosion and token overflow.
- **Implement:** Chunking pipeline, semantic chunking, rolling memory compression, token estimation, safe context budgets, intermediate summary persistence, grouped synthesis.
- **Strict Rule:** NEVER keep full raw article contents, all summaries, or entire execution histories inside the LangGraph state. LangGraph state must remain lightweight.

## 5. Database Responsibilities
**Redis:**
- Caching & streaming state.
- Temporary memory and intermediate summaries.
- Resumable execution state and distributed coordination.

**PostgreSQL:**
- Persistent research history.
- Execution logs & audit logs.
- User sessions & saved reports.
- Analytics and feature metadata.

## 6. Feature Flag System
Centralized feature flag and configuration architecture for both frontend and backend.
- Examples: `ENABLE_STREAMING`, `ENABLE_REDIS_CACHE`, `ENABLE_PARALLEL_SUMMARIZATION`, `ENABLE_GROUP_SYNTHESIS`, `ENABLE_OBSERVABILITY`, `ENABLE_SOURCE_PREVIEW`.
- Configs must be environment-based, globally manageable, and support scalable feature rollout.

## 7. Architecture & Code Quality Principles
- **Architecture:** Modular monolith, service-oriented structure, strict typing, separation of concerns, scalable folder structure. No spaghetti code or giant files.
- **Async-First:** Use asyncio, async DB sessions, async streaming, and async HTTP requests. Avoid blocking operations.
- **Streaming:** FastAPI SSE must support real-time updates, reconnect handling, heartbeat events, and cancellation handling.
- **Code Quality:** Meaningful comments, type safety, reusable architecture, production maintainable. Avoid hardcoded values and hidden side effects.

## 8. Project Phases
- **Phase 1:** Core Monorepo & Infrastructure Foundation
- **Phase 2:** Database & Persistence Architecture
- **Phase 3:** LangGraph Multi-Agent System
- **Phase 4:** Token-Safe Research Processing Pipeline
- **Phase 5:** FastAPI SSE Streaming Architecture
- **Phase 6:** Next.js Real-Time Research UI
- **Phase 7:** Redis Cache & Distributed State Layer
- **Phase 8:** Production Hardening & Reliability
- **Phase 9:** Observability, Analytics & Monitoring
- **Phase 10:** Deployment & DevOps
