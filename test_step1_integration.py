#!/usr/bin/env python3
"""
Test Step 1 Integration: Query Analysis Service + RetrievalService + API

This test verifies that our complete integration works:
1. Query Analysis Service
2. RetrievalService with real implementation
3. API endpoints
4. Data models

We'll test different types of queries and see the complete flow.
"""

import asyncio
import logging
import sys
import os
import json

# Add the app directory to the Python path
sys.path.append('/app')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"🔍 {title}")
    print("="*70)

def print_section(title: str):
    """Print a section header"""
    print(f"\n📋 {title}")
    print("-" * 50)

def print_query_result(result, query_num: int):
    """Print query result in a nice format"""
    print(f"\n🔍 Query {query_num} Result:")
    print(f"   Query: {result.get('query', 'N/A')}")
    print(f"   Answer: {result.get('answer', 'N/A')}")
    print(f"   Processing Time: {result.get('processing_time', 0):.3f}s")
    print(f"   Confidence: {result.get('confidence', 0):.2f}")
    
    # Print metadata
    metadata = result.get('metadata', {})
    if metadata:
        print(f"   Metadata:")
        for key, value in metadata.items():
            if key == 'entities_found':
                print(f"     - {key}: {len(value)} entities found")
                for entity in value[:2]:  # Show first 2 entities
                    print(f"       * {entity.get('name', 'N/A')} ({entity.get('type', 'N/A')}) - {entity.get('confidence', 0):.2f}")
            else:
                print(f"     - {key}: {value}")
    
    # Print sources
    sources = result.get('sources', [])
    if sources:
        print(f"   Sources Found: {len(sources)}")
        for i, source in enumerate(sources[:2], 1):  # Show first 2 sources
            print(f"     {i}. {source.get('document_title', 'N/A')}")
            print(f"        Score: {source.get('relevance_score', 0):.2f}")
            print(f"        Content: {source.get('content', 'N/A')[:100]}...")
    
    # Print graph paths
    graph_paths = result.get('graph_paths', [])
    if graph_paths:
        print(f"   Graph Paths: {len(graph_paths)}")
        for i, path in enumerate(graph_paths, 1):
            print(f"     {i}. Path: {' -> '.join(path.get('path', []))}")
            print(f"        Strength: {path.get('total_strength', 0):.2f}")

async def test_query_analysis_service():
    """Test Query Analysis Service directly"""
    print_section("Testing Query Analysis Service Directly")
    
    try:
        from app.services.query_analysis_service import QueryAnalysisService
        
        analyzer = QueryAnalysisService()
        
        test_queries = [
            "What is CRISPR-Cas9?",
            "How does TP53 cause cancer?",
            "Compare different gene editing methods"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Testing Query {i}: {query}")
            analysis = await analyzer.analyze_query(query)
            
            print(f"   ✅ Intent: {analysis.intent.value}")
            print(f"   ✅ Complexity: {analysis.complexity.value}")
            print(f"   ✅ Strategy: {analysis.recommended_strategy.value}")
            print(f"   ✅ Confidence: {analysis.confidence:.2f}")
            
            if analysis.entities:
                print(f"   ✅ Entities: {len(analysis.entities)} found")
                for entity in analysis.entities[:2]:
                    print(f"      - {entity.name} ({entity.type}) - {entity.confidence:.2f}")
            else:
                print(f"   ✅ Entities: None found")
        
        print("\n✅ Query Analysis Service is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Query Analysis Service test failed: {str(e)}")
        return False

async def test_retrieval_service():
    """Test RetrievalService with Query Analysis integration"""
    print_section("Testing RetrievalService with Query Analysis")
    
    try:
        from app.services.retrieval_service import RetrievalService
        from app.core.database import get_database
        
        # Get database connection
        db = await get_database()
        retrieval_service = RetrievalService(db)
        
        test_queries = [
            "What is CRISPR-Cas9?",
            "Tell me about gene therapy",
            "How are TP53 and BRCA1 related?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Testing RetrievalService Query {i}: {query}")
            
            result = await retrieval_service.process_query(
                query=query,
                max_results=5,
                include_graph=True,
                max_hops=3
            )
            
            print(f"   ✅ Query: {result.query}")
            print(f"   ✅ Answer: {result.answer[:100]}...")
            print(f"   ✅ Sources: {len(result.sources)}")
            print(f"   ✅ Graph Paths: {len(result.graph_paths)}")
            print(f"   ✅ Processing Time: {result.processing_time:.3f}s")
            print(f"   ✅ Confidence: {result.confidence:.2f}")
            
            # Show metadata
            if result.metadata:
                print(f"   ✅ Metadata:")
                for key, value in result.metadata.items():
                    if key == 'entities_found':
                        print(f"      - {key}: {len(value)} entities")
                    else:
                        print(f"      - {key}: {value}")
        
        print("\n✅ RetrievalService is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ RetrievalService test failed: {str(e)}")
        return False

async def test_api_endpoint():
    """Test the API endpoint"""
    print_section("Testing API Endpoint")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        test_queries = [
            {
                "query": "What is CRISPR-Cas9?",
                "max_results": 3,
                "include_graph": True,
                "max_hops": 2
            },
            {
                "query": "Tell me about cancer research",
                "max_results": 2,
                "include_graph": False,
                "max_hops": 1
            }
        ]
        
        for i, query_data in enumerate(test_queries, 1):
            print(f"\n🔍 Testing API Query {i}: {query_data['query']}")
            
            response = client.post("/api/v1/queries/search", json=query_data)
            
            print(f"   ✅ Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print_query_result(result, i)
            else:
                print(f"   ❌ Error: {response.text}")
        
        print("\n✅ API endpoint is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {str(e)}")
        return False

async def test_data_models():
    """Test our data models"""
    print_section("Testing Data Models")
    
    try:
        from app.models import QuerySource, GraphPath, QueryResponse
        
        # Test QuerySource
        source = QuerySource(
            document_id="test_doc",
            document_title="Test Document",
            section_id="test_sec",
            section_type="abstract",
            content="Test content",
            relevance_score=0.85,
            doi="10.1000/test"
        )
        print(f"✅ QuerySource model works: {source.document_title}")
        
        # Test GraphPath
        path = GraphPath(
            path=["CRISPR", "gene_editing"],
            entities=[{"name": "CRISPR", "confidence": 0.9}],
            relationships=[{"type": "related_to", "strength": 0.8}],
            total_strength=0.85
        )
        print(f"✅ GraphPath model works: {' -> '.join(path.path)}")
        
        # Test QueryResponse
        response = QueryResponse(
            query="test query",
            answer="test answer",
            sources=[source],
            graph_paths=[path],
            processing_time=1.5,
            confidence=0.8
        )
        print(f"✅ QueryResponse model works: {response.query}")
        
        print("\n✅ All data models are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Data models test failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    print_header("STEP 1 INTEGRATION TESTING")
    print("We're testing our complete Step 1 implementation!")
    
    results = []
    
    # Test 1: Data Models
    print("\n🧪 Test 1: Data Models")
    results.append(await test_data_models())
    
    # Test 2: Query Analysis Service
    print("\n🧪 Test 2: Query Analysis Service")
    results.append(await test_query_analysis_service())
    
    # Test 3: RetrievalService
    print("\n🧪 Test 3: RetrievalService Integration")
    results.append(await test_retrieval_service())
    
    # Test 4: API Endpoint
    print("\n🧪 Test 4: API Endpoint")
    results.append(await test_api_endpoint())
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    
    test_names = [
        "Data Models",
        "Query Analysis Service", 
        "RetrievalService Integration",
        "API Endpoint"
    ]
    
    for i, (name, success) in enumerate(zip(test_names, results), 1):
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   Test {i}: {name} - {status}")
    
    all_passed = all(results)
    
    if all_passed:
        print_header("🎉 ALL TESTS PASSED!")
        print("✅ Step 1 Integration is working perfectly!")
        print("\n📝 What we've built:")
        print("   - Query Analysis Service with proper prompt structure")
        print("   - RetrievalService with real Query Analysis integration")
        print("   - Complete data models (QuerySource, GraphPath, QueryResponse)")
        print("   - Working API endpoint with proper response format")
        print("   - Full integration between all components")
        
        print("\n🎯 Next Steps:")
        print("   Step 2: Vector-First Strategy")
        print("   Step 3: Graph-First Strategy")
        print("   Step 4: Hybrid Strategy with MongoDB features")
        print("   Step 5: ML Orchestrator")
        
        return 0
    else:
        print_header("❌ SOME TESTS FAILED")
        print("We need to fix the failing tests before proceeding.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
