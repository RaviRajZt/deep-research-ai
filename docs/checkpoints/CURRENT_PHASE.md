# Current Phase Tracker

**Active Phase:** Phase 7 — Redis Cache & Distributed State Layer  
**Previous Phase:** ✅ Phase 6 — Next.js Real-Time Research UI (COMPLETE)  
**Status:** Local Open-Source Infrastructure Integrated (Ollama Gemma + SearXNG Web Search Live)

## 🎯 Phase Objectives
- Implement scalable, high-throughput distributed memory and caching layer using Redis
- Support query result caching to avoid redundant search agent operations
- Support intermediate summary caching to avoid expensive LLM chunk re-summarization
- Build a distributed run state repository to track real-time agent execution across multiple workers
- Introduce resumable execution support enabling research runs to resume from their last saved agent checkpoint
- Enforce strict TTL management and selective cache invalidation strategies

## 📋 Task Checklist
- [ ] Design and implement a reusable `RedisCacheService` in the backend
- [ ] Create query cache decorators or interceptors for the search agent
- [ ] Integrate intermediate summary caching inside the `ChunkSummarizerPipeline`
- [ ] Design a distributed run state repository in Redis to persist graph checkpoint states
- [ ] Connect LangGraph's checkpointer mechanism to the Redis distributed state layer to enable resumability
- [ ] Define TTL constraints (e.g., 24h for queries, 7d for summaries) and manual invalidation utilities
- [ ] Write a comprehensive test suite validating cache hits, misses, TTL expiries, and session resumption

## 🏗️ Phase Architectural Decisions
- **Unified Redis Connection:** Share a connection pool via FastAPI dependency injection and singleton client management.
- **State Serialization:** Graph state checkpoints are serialized using JSON/binary format and saved under specific session key groups.
- **Resumption Safeguards:** Ensure that if a session halts or times out, the user can click "Resume Investigation" in the Next.js UI, triggering the supervisor agent to resume execution from the exact failed step rather than restarting the entire graph.

## ✅ Validation Checklist
- [ ] Cache hits are verified via debug logs and metrics output
- [ ] Selective cache invalidation (by session or global) purges database keys reliably
- [ ] Simulated agent container failure successfully resumes execution from the last checkpoint with no data loss

## 🚧 Blockers / Notes
- The Redis container is fully operational inside the local development environment (`docker compose`).
- All 28 current unit and integration tests are passing cleanly.
