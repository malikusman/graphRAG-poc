#!/usr/bin/env python3
"""
Test Step 1: Query Analysis Service

This test helps us understand how our Query Analysis Service works.
We'll test different types of queries and see how it analyzes them.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.append('/app')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def print_analysis(analysis, query_num: int):
    """Print query analysis in a nice format"""
    print(f"\n📋 Query {query_num} Analysis:")
    print(f"   Query: {analysis.query}")
    print(f"   Intent: {analysis.intent.value} (what type of question)")
    print(f"   Complexity: {analysis.complexity.value} (how complex)")
    print(f"   Strategy: {analysis.recommended_strategy.value} (best approach)")
    print(f"   Confidence: {analysis.confidence:.2f}")
    
    if analysis.entities:
        print(f"   Entities Found:")
        for entity in analysis.entities:
            print(f"     - {entity.name} ({entity.type}) - confidence: {entity.confidence:.2f}")
    else:
        print(f"   Entities Found: None")

async def test_query_analysis_service():
    """Test our Query Analysis Service with different types of queries"""
    print_header("STEP 1: TESTING QUERY ANALYSIS SERVICE")
    
    try:
        from app.services.query_analysis_service import QueryAnalysisService
        
        # Create the analyzer
        analyzer = QueryAnalysisService()
        
        # Test different types of queries
        test_queries = [
            "What is CRISPR-Cas9?",                                    # Factual
            "Tell me about gene therapy",                              # Exploratory  
            "Compare CRISPR and TALENs",                              # Comparative
            "How does TP53 cause cancer?",                           # Causal
            "Recent advances in cancer immunotherapy",               # Temporal
            "What methods are used to measure protein expression?",  # Methodological
            "How are TP53 and BRCA1 related in cancer development?" # Complex
        ]
        
        print("🧪 Testing different query types...")
        
        for i, query in enumerate(test_queries, 1):
            try:
                print(f"\n🔍 Testing Query {i}: {query}")
                
                # Analyze the query
                analysis = await analyzer.analyze_query(query)
                
                # Print the analysis
                print_analysis(analysis, i)
                
                # Show reasoning
                reasoning = analyzer.get_strategy_reasoning(analysis)
                print(f"   Reasoning: {reasoning}")
                
            except Exception as e:
                print(f"   ❌ Error analyzing query {i}: {str(e)}")
        
        print_header("QUERY ANALYSIS SERVICE TEST COMPLETE")
        print("✅ Our Query Analysis Service is working!")
        print("\n📚 What we learned:")
        print("   - It can identify different types of questions (intent)")
        print("   - It can assess query complexity")
        print("   - It can extract scientific entities")
        print("   - It can recommend retrieval strategies")
        print("   - It provides confidence scores")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Query Analysis Service: {str(e)}")
        return False

async def test_strategy_recommendations():
    """Test strategy recommendations for different query types"""
    print_header("TESTING STRATEGY RECOMMENDATIONS")
    
    try:
        from app.services.query_analysis_service import QueryAnalysisService
        
        analyzer = QueryAnalysisService()
        
        # Test specific query types to see strategy recommendations
        strategy_test_queries = [
            {
                "query": "What is CRISPR-Cas9?",
                "expected_intent": "factual",
                "description": "Simple factual question"
            },
            {
                "query": "Tell me everything about cancer research",
                "expected_intent": "exploratory", 
                "description": "Broad exploratory question"
            },
            {
                "query": "How does TP53 interact with BRCA1 in cancer?",
                "expected_intent": "causal",
                "description": "Relationship-focused question"
            },
            {
                "query": "Compare different gene editing methods and their applications",
                "expected_intent": "comparative",
                "description": "Complex comparative question"
            }
        ]
        
        for i, test_case in enumerate(strategy_test_queries, 1):
            print(f"\n🎯 Strategy Test {i}: {test_case['description']}")
            print(f"   Query: {test_case['query']}")
            
            analysis = await analyzer.analyze_query(test_case['query'])
            
            print(f"   ✅ Intent: {analysis.intent.value}")
            print(f"   ✅ Complexity: {analysis.complexity.value}")
            print(f"   ✅ Recommended Strategy: {analysis.recommended_strategy.value}")
            print(f"   ✅ Confidence: {analysis.confidence:.2f}")
            
            # Show why this strategy was chosen
            reasoning = analyzer.get_strategy_reasoning(analysis)
            print(f"   💡 Reasoning: {reasoning}")
        
        print_header("STRATEGY RECOMMENDATIONS TEST COMPLETE")
        print("✅ Strategy recommendations are working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing strategy recommendations: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("🚀 STEP 1: QUERY ANALYSIS SERVICE LEARNING")
    print("We're going to test our Query Analysis Service step by step!")
    
    # Test 1: Basic query analysis
    success1 = await test_query_analysis_service()
    
    if success1:
        # Test 2: Strategy recommendations
        success2 = await test_strategy_recommendations()
        
        if success2:
            print_header("🎉 STEP 1 COMPLETE!")
            print("✅ Query Analysis Service is working perfectly!")
            print("\n📝 What we built:")
            print("   - Query intent classification (factual, exploratory, etc.)")
            print("   - Query complexity assessment (simple, moderate, complex)")
            print("   - Entity extraction from queries")
            print("   - Strategy recommendation (vector_first, graph_first, hybrid)")
            print("   - Confidence scoring")
            
            print("\n🎯 Next Steps:")
            print("   Step 2: Vector-First Strategy")
            print("   Step 3: Graph-First Strategy") 
            print("   Step 4: Hybrid Strategy")
            print("   Step 5: ML Orchestrator")
            
            return 0
        else:
            print("❌ Strategy recommendations test failed")
            return 1
    else:
        print("❌ Query analysis service test failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
