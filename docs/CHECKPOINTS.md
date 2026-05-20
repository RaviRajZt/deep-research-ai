# Global Project Checkpoints

This file tracks the high-level progress of the Anti-Gravity AI Research Platform across all project phases. For granular, task-by-task tracking of the currently active phase, refer to `docs/checkpoints/CURRENT_PHASE.md`.

## Phase Tracking

- [ ] **Phase 1:** Core Monorepo & Infrastructure Foundation
- [ ] **Phase 2:** Database & Persistence Architecture
- [ ] **Phase 3:** LangGraph Multi-Agent System
- [ ] **Phase 4:** Token-Safe Research Processing Pipeline
- [ ] **Phase 5:** FastAPI SSE Streaming Architecture
- [ ] **Phase 6:** Next.js Real-Time Research UI
- [ ] **Phase 7:** Redis Cache & Distributed State Layer
- [ ] **Phase 8:** Production Hardening & Reliability
- [ ] **Phase 9:** Observability, Analytics & Monitoring
- [ ] **Phase 10:** Deployment & DevOps

## Global Architectural Decisions
*(Log major cross-cutting decisions here)*
- **Model:** Gemma 4 E4B (128k context)
- **State Management:** LangGraph state kept lightweight; heavy payload/raw text offloaded to Redis/Postgres.
- **Streaming:** Server-Sent Events (SSE) from FastAPI to Next.js.

## Technical Debt & Known Risks
*(Log identified risks and areas needing future refactoring)*
- *None currently identified.*

## Future Enhancements
*(Log ideas that are out of scope for the current phases but valuable for the future)*
- *None currently identified.*
