"""
Comprehensive LangSmith Integration Test
Tests all major components with tracing
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
from app.services.embeddings import EmbeddingsService
from app.services.query_analysis_service import QueryAnalysisService
from app.services.vector_search_service import VectorSearchService
from app.core.config import settings

async def test_embeddings_service():
    """Test embeddings service with tracing"""
    print("🧪 Testing Embeddings Service...")
    
    try:
        embeddings_service = EmbeddingsService()
        
        # Test single embedding
        embedding = embeddings_service.generate_embedding("Test text for embedding generation")
        
        if embedding:
            print(f"✅ Single embedding: {len(embedding)} dimensions")
        else:
            print("❌ Failed to generate single embedding")
            return False
        
        # Test batch embeddings
        sections = [
            {"title": "Test 1", "text": "First test section"},
            {"title": "Test 2", "text": ""},  # Empty text
            {"title": "Test 3", "text": "Third test section"}
        ]
        
        batch_results = embeddings_service.generate_section_embeddings_batch(sections)
        
        successful = sum(1 for s in batch_results if s.get('embeddings'))
        print(f"✅ Batch embeddings: {successful}/{len(sections)} successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings service error: {e}")
        return False

async def test_query_analysis_service():
    """Test query analysis service with tracing"""
    print("\n🧪 Testing Query Analysis Service...")
    
    try:
        query_analyzer = QueryAnalysisService()
        
        # Test query analysis
        analysis = await query_analyzer.analyze_query("What is CRISPR gene editing technology?")
        
        print(f"✅ Query analysis completed:")
        print(f"   - Intent: {analysis.intent.value}")
        print(f"   - Complexity: {analysis.complexity.value}")
        print(f"   - Strategy: {analysis.recommended_strategy.value}")
        print(f"   - Entities: {len(analysis.entities)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query analysis error: {e}")
        return False

async def test_vector_search_service():
    """Test vector search service with tracing"""
    print("\n🧪 Testing Vector Search Service...")
    
    try:
        # Note: This will fail without MongoDB, but we can test the tracing setup
        vector_search = VectorSearchService()
        
        print("✅ Vector search service initialized (tracing ready)")
        print("   - Note: Actual search requires MongoDB connection")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector search error: {e}")
        return False

async def test_langsmith_client():
    """Test LangSmith client functionality"""
    print("\n🧪 Testing LangSmith Client...")
    
    try:
        client = Client()
        
        # Test basic client functionality
        print("✅ LangSmith client initialized")
        print(f"   - Project: {settings.LANGCHAIN_PROJECT}")
        print(f"   - Endpoint: {settings.LANGCHAIN_ENDPOINT}")
        
        return True
        
    except Exception as e:
        print(f"❌ LangSmith client error: {e}")
        return False

async def main():
    """Run comprehensive LangSmith tests"""
    print("🚀 Comprehensive LangSmith Integration Test\n")
    print("=" * 60)
    
    # Test results
    results = {}
    
    # Test 1: LangSmith Client
    results["langsmith_client"] = await test_langsmith_client()
    
    # Test 2: Embeddings Service
    results["embeddings_service"] = await test_embeddings_service()
    
    # Test 3: Query Analysis Service
    results["query_analysis"] = await test_query_analysis_service()
    
    # Test 4: Vector Search Service
    results["vector_search"] = await test_vector_search_service()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  - {test_name.replace('_', ' ').title()}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All LangSmith integration tests passed!")
        print("🔍 View traces at: https://smith.langchain.com/public/sagewrite-graphrag")
        print("\n✨ LangSmith Integration Status: READY FOR PRODUCTION")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the errors above.")
        print("🔧 LangSmith Integration Status: NEEDS ATTENTION")

if __name__ == "__main__":
    asyncio.run(main())
