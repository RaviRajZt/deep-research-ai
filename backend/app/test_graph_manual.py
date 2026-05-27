import asyncio
import uuid
from app.graph.builder import build_research_graph
from app.redis_.client import init_redis, close_redis
from app.core.settings import get_settings

class MockRepo:
    async def append_step(self, **kwargs):
        class Log:
            id = uuid.uuid4()
        print(f"[ExecutionLogRepo] Append Step: {kwargs}")
        return Log()
        
    async def complete_step(self, **kwargs):
        print(f"[ExecutionLogRepo] Complete Step: {kwargs}")
        
    async def fail_step(self, **kwargs):
        print(f"[ExecutionLogRepo] Fail Step: {kwargs}")


class MockSessionRepo:
    async def update_status(self, session_id, status):
        print(f"[SessionRepo] Status Update: {status}")
        
    async def set_result(self, session_id, result_summary, result_token_count):
        print(f"[SessionRepo] Set Result: token_count={result_token_count}")
        print(f"\n=================== FINAL REPORT SUMMARY ===================")
        print(result_summary)
        print(f"===========================================================\n")


class MockSourceRepo:
    def __init__(self):
        self.db = {}

    async def bulk_create(self, sources):
        class Source:
            def __init__(self, s):
                self.id = uuid.uuid4()
                self.title = f"Telemetry Page for {s.get('url', 'source')}"
                self.source_metadata = {}
                self.fetch_status = "pending"
                self.__dict__.update(s)
        res = [Source(s) for s in sources]
        for src in res:
            self.db[src.id] = src
        print(f"[SourceRepo] Bulk created {len(res)} sources")
        return res
        
    async def get_by_id(self, source_id):
        return self.db.get(source_id)

    async def get_by_session(self, session_id, fetch_status=None):
        res = []
        for src in self.db.values():
            if src.session_id == session_id:
                if fetch_status is None or src.fetch_status == fetch_status:
                    res.append(src)
        return res

    async def update_fetch_status(self, source_id, **kwargs):
        src = self.db.get(source_id)
        if src:
            src.__dict__.update(kwargs)
        print(f"[SourceRepo] Update fetch status: {kwargs}")
        
    async def update(self, entity_id, **kwargs):
        src = self.db.get(entity_id)
        if src:
            src.__dict__.update(kwargs)
        print(f"[SourceRepo] Update source={entity_id}: {kwargs}")


async def main():
    print("Initializing Redis for manual test graph run...")
    settings = get_settings()
    await init_redis(settings)

    print("Building graph...")
    source_repo = MockSourceRepo()
    graph = build_research_graph(
        execution_log_repo=MockRepo(),
        session_repo=MockSessionRepo(),
        source_repo=source_repo
    )
    
    session_id = uuid.uuid4()
    initial_state = {
        "session_id": session_id,
        "topic": "Quantum Computing Scalability",
        "current_step": "init",
        "next_agent": "",
        "source_ids": [],
        "summary_ids": [],
        "errors": [],
        "result_summary": None,
    }
    
    print("Running graph...")
    try:
        async for output in graph.astream(initial_state):
            print("\n--- STATE OUTPUT ---")
            print(output)
            print("--------------------\n")
    finally:
        print("Closing Redis...")
        await close_redis()

if __name__ == "__main__":
    asyncio.run(main())
