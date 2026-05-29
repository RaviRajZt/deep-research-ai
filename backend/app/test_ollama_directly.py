import asyncio
import sys
import os
import time

# Add backend directory to sys.path so we can run this script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm import LLMService

async def test_ollama():
    print("--------------------------------------------------")
    print("Testing LLMService / Ollama connection...")
    print("--------------------------------------------------")
    
    # Initialize LLMService.
    # Note: We must ensure sys.modules does NOT contain "pytest" so it initializes ChatOpenAI instead of mock.
    if "pytest" in sys.modules:
        sys.modules.pop("pytest")
        
    start_time = time.time()
    try:
        service = LLMService()
        print(f"LLMService initialized. Model: {service.model_name}, Ollama Model: {service.ollama_model}")
        print(f"Ollama Base URL: {service.ollama_base_url}")
        
        test_text = (
            "Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics "
            "to solve problems too complex for classical computers. Today, IBM Quantum makes real quantum hardware "
            "available to hundreds of thousands of developers."
        )
        
        print("\nSending a test summarization request to Ollama...")
        t0 = time.time()
        summary = await service.summarize_text(test_text, context_hint="quantum computing basics")
        t1 = time.time()
        
        print("\n--- OLLAMA RESPONSE ---")
        print(summary)
        print("-----------------------")
        print(f"Time taken: {t1 - t0:.2f} seconds")
        print("Ollama test SUCCESSFUL!")
        
    except Exception as e:
        print(f"\n❌ Error during Ollama test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
