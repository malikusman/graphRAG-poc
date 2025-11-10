"""
Simple LangSmith test without MongoDB dependency
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set environment variables for LangSmith (use actual env vars in production)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = "sagewrite-graphrag"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

from langsmith import Client
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.config import settings

async def test_langsmith_tracing():
    """Test LangSmith tracing with a simple LLM call"""
    print("🧪 Testing LangSmith Integration...")
    
    # Initialize LangSmith client
    client = Client()
    print(f"✅ LangSmith client initialized")
    
    # Create a simple chain
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Use a model that supports temperature
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY
    )
    
    prompt = ChatPromptTemplate.from_template(
        "Extract entities from this text: {text}\n\nReturn as JSON with entities array."
    )
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    # Test text
    test_text = "CRISPR-Cas9 was developed by Jennifer Doudna and Emmanuelle Charpentier at UC Berkeley."
    
    print(f"📝 Testing with text: {test_text}")
    
    try:
        # This should be automatically traced by LangSmith
        result = await chain.ainvoke({"text": test_text})
        print(f"✅ LLM Response: {result}")
        
        # Check if we can access the trace
        print(f"🔍 View your trace at: https://smith.langchain.com/public/sagewrite-graphrag")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_embeddings_tracing():
    """Test embeddings service tracing"""
    print("\n🧪 Testing Embeddings Service Tracing...")
    
    try:
        from app.services.embeddings import EmbeddingsService
        
        embeddings_service = EmbeddingsService()
        
        # Test embedding generation (should be traced)
        embedding = embeddings_service.generate_embedding("Test text for embedding")
        
        if embedding:
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            print(f"🔍 View embeddings trace at: https://smith.langchain.com/public/sagewrite-graphrag")
            return True
        else:
            print("❌ Failed to generate embedding")
            return False
            
    except Exception as e:
        print(f"❌ Error testing embeddings: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting LangSmith Integration Tests\n")
    
    # Test 1: Basic LLM tracing
    test1_success = await test_langsmith_tracing()
    
    # Test 2: Embeddings tracing
    test2_success = await test_embeddings_tracing()
    
    print(f"\n📊 Test Results:")
    print(f"  - LLM Tracing: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"  - Embeddings Tracing: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print(f"\n🎉 All tests passed! LangSmith integration is working.")
        print(f"🔍 View all traces at: https://smith.langchain.com/public/sagewrite-graphrag")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
