import asyncio
import sys
import os
import uuid
import time

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.graph.builder import build_research_graph
from app.redis_.client import init_redis, close_redis
from app.core.settings import get_settings

# Simple Mock repositories to run without database dependencies or side effects
class MockExecutionLogRepo:
    async def append_step(self, **kwargs):
        class Log:
            id = uuid.uuid4()
        print(f"  [ExecutionLogRepo] Append Step: {kwargs.get('agent_role')} -> {kwargs.get('message')}")
        return Log()
        
    async def complete_step(self, **kwargs):
        print(f"  [ExecutionLogRepo] Complete Step: {kwargs.get('message')}")
        
    async def fail_step(self, **kwargs):
        print(f"  [ExecutionLogRepo] Fail Step: {kwargs.get('error_detail')}")


class MockSessionRepo:
    async def update_status(self, session_id, status):
        print(f"  [SessionRepo] Status Update: {status}")
        
    async def set_result(self, session_id, result_summary, result_token_count):
        print(f"  [SessionRepo] Set Result: token_count={result_token_count}")
        print(f"\n=================== FINAL GENERATED REPORT ===================")
        print(result_summary)
        print(f"==============================================================\n")


class MockSourceRepo:
    def __init__(self):
        self.db = {}

    async def bulk_create(self, sources):
        class Source:
            def __init__(self, s):
                self.id = uuid.uuid4()
                self.title = s.get('title', 'Source')
                self.url = s.get('url', 'url')
                self.source_metadata = {}
                self.fetch_status = "pending"
                self.__dict__.update(s)
        res = [Source(s) for s in sources]
        for src in res:
            self.db[src.id] = src
        print(f"  [SourceRepo] Bulk created {len(res)} sources")
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
        print(f"  [SourceRepo] Update fetch status: {kwargs.get('fetch_status')}")
        
    async def update(self, entity_id, **kwargs):
        src = self.db.get(entity_id)
        if src:
            src.__dict__.update(kwargs)
            # Update fetch status to "fetched" when it is successfully summarized
            src.fetch_status = "fetched"
        print(f"  [SourceRepo] Update source metrics: {kwargs}")


async def main():
    print("==================================================")
    print("Testing Full Agent Flow with Ollama...")
    print("==================================================")
    
    # 1. Initialize Redis
    settings = get_settings()
    await init_redis(settings)
    
    # 2. Build graph with our Mock Repositories
    source_repo = MockSourceRepo()
    graph = build_research_graph(
        execution_log_repo=MockExecutionLogRepo(),
        session_repo=MockSessionRepo(),
        source_repo=source_repo
    )
    
    # 3. Create initial state
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
    
    # We will temporarily monkeypatch the web scraping to return a small high-fidelity text block
    # so that the summarization runs quickly (only 1 chunk) during this integration verification.
    import httpx
    original_get = httpx.AsyncClient.get
    
    async def mock_get(self_client, url, *args, **kwargs):
        class MockResponse:
            status_code = 200
            text = (
                "Quantum computing scalability relies on developing stable qubits and error-correction methods. "
                "Current physical qubits are prone to environmental noise, requiring logical qubits composed of thousands "
                "of physical ones to achieve fault tolerance. Scalability also demands efficient control wiring and cryogenic architectures "
                "to handle the low temperatures needed for superconducting circuits. Without scaling physical structures and software logic, "
                "quantum computers will not surpass classical computational limits for practical applications."
            )
        return MockResponse()
    
    httpx.AsyncClient.get = mock_get
    
    # Also ensure sys.modules does NOT contain "pytest" so LLMService initializes the real Ollama ChatOpenAI
    if "pytest" in sys.modules:
        sys.modules.pop("pytest")
    
    # 4. Stream the graph execution
    start_time = time.time()
    try:
        print("\nStarting LangGraph streaming...")
        async for output in graph.astream(initial_state):
            print(f"\n--- Node Output: {list(output.keys())} ---")
            for node, state_update in output.items():
                print(f"Node '{node}' update keys: {list(state_update.keys())}")
            print("------------------------------------\n")
            
        print(f"🎉 End-to-End Agent Flow Test completed in {time.time() - start_time:.2f} seconds!")
        
    except Exception as e:
        print(f"\n❌ Error during graph flow execution: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original httpx.AsyncClient.get
        httpx.AsyncClient.get = original_get
        await close_redis()

if __name__ == "__main__":
    asyncio.run(main())
