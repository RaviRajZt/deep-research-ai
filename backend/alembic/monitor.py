import asyncio
import time
import sys
from app.core.settings import get_settings
from app.db.session import get_session_factory
from app.models.research_session import ResearchSession
from app.models.source import Source
from sqlalchemy import select

async def main():
    settings = get_settings()
    factory = get_session_factory(settings)
    
    print("=== Deep Research Telemetry Monitor ===", flush=True)
    
    start_time = time.time()
    while True:
        try:
            async with factory() as db:
                # Query session
                res = await db.execute(select(ResearchSession))
                sessions = res.scalars().all()
                if not sessions:
                    print("No active research sessions in database.", flush=True)
                    await asyncio.sleep(15)
                    continue
                    
                session = sessions[0]
                
                # Query sources
                res_sources = await db.execute(select(Source).where(Source.session_id == session.id))
                sources = res_sources.scalars().all()
                
                elapsed = time.time() - start_time
                print(f"[{elapsed:.1f}s] Session: '{session.topic}' | ID: {session.id} | Status: {session.status.upper()}", flush=True)
                
                for idx, s in enumerate(sources):
                    print(f"  -> Source {idx+1}: {s.title[:50]}... | Fetch: {s.fetch_status} | Chunks: {s.chunk_count}", flush=True)
                
                if session.status == "completed":
                    print("\n🎉 WORKFLOW SUCCESSFULLY COMPLETED!", flush=True)
                    print("\n=== FINAL SYNTHESIZED ARTICLE SUMMARY BRIEF ===", flush=True)
                    print(session.result_summary, flush=True)
                    break
                elif session.status == "failed":
                    print(f"\n❌ WORKFLOW FAILED: {session.error_message}", flush=True)
                    break
                    
        except Exception as e:
            print(f"Error reading database: {e}", flush=True)
            
        await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
