#!/usr/bin/env python3
"""
Test GraphRAG Retrieval Service - Graph-First Strategy

This test demonstrates how the retrieval service works with the graph-first approach:
1. Analyzes a query to understand intent and entities
2. Uses graph traversal to find relevant paths
3. Converts graph paths to document sources
4. Returns ranked results with detailed metadata

We'll test with the entities and relationships we have in our database from the previous test.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Override the MongoDB URL environment variable before importing app modules
os.environ["MONGODB_URL"] = "mongodb://localhost:27017/sagewrite"

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_database
from app.services.retrieval_service import RetrievalService
from app.services.query_analysis_service import QueryAnalysisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_retrieval_service():
    """Test the retrieval service with graph-first strategy"""
    logger.info("🚀 Starting Retrieval Service Test")
    
    try:
        # Get database connection
        db = await get_database()
        logger.info("✅ Database connection established")
        
        # Initialize retrieval service
        retrieval_service = RetrievalService(db)
        logger.info("✅ RetrievalService initialized")
        
        # Initialize query analysis service
        query_analyzer = QueryAnalysisService()
        logger.info("✅ QueryAnalysisService initialized")
        
        # Test queries that should work well with graph-first strategy
        test_queries = [
            # Single entity exploration
            "What does CRISPR-Cas9 target?",
            
            # Entity pair relationship
            "How does TP53 affect cancer?",
            
            # Multi-entity analysis
            "How are CRISPR-Cas9, TP53, and cancer related?",
            
            # Causal relationship
            "How does TP53 restoration decrease cell proliferation?",
            
            # Exploratory query
            "What treatments are available for cancer?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"🔍 TEST QUERY {i}: {query}")
            logger.info(f"{'='*80}")
            
            # Step 1: Analyze the query
            logger.info("📊 Step 1: Analyzing query...")
            analysis = await query_analyzer.analyze_query(query)
            
            logger.info(f"Query Analysis Results:")
            logger.info(f"  Intent: {analysis.intent.value}")
            logger.info(f"  Complexity: {analysis.complexity.value}")
            logger.info(f"  Recommended Strategy: {analysis.recommended_strategy.value}")
            logger.info(f"  Confidence: {analysis.confidence:.2f}")
            logger.info(f"  Entities Found: {len(analysis.entities)}")
            
            for j, entity in enumerate(analysis.entities, 1):
                logger.info(f"    {j}. {entity.name} ({entity.type}) - Confidence: {entity.confidence:.2f}")
            
            # Step 2: Process query with retrieval service
            logger.info("\n🔍 Step 2: Processing query with retrieval service...")
            start_time = datetime.now()
            
            response = await retrieval_service.process_query(
                query=query,
                max_results=5,
                include_graph=True,
                max_hops=3
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Step 3: Display results
            logger.info(f"\n📊 Step 3: Retrieval Results (Duration: {duration:.2f}s)")
            logger.info(f"Strategy Used: {response.metadata.get('strategy_used', 'N/A')}")
            logger.info(f"Total Sources: {len(response.sources)}")
            logger.info(f"Processing Time: {response.processing_time:.3f}s")
            logger.info(f"Confidence: {response.confidence:.2f}")
            logger.info(f"Answer: {response.answer}")
            
            if response.sources:
                logger.info("\n📚 Retrieved Sources:")
                for j, source in enumerate(response.sources, 1):
                    logger.info(f"\n  {j}. Document: {source.document_title}")
                    logger.info(f"     Section: {source.section_type}")
                    logger.info(f"     Relevance Score: {source.relevance_score:.3f}")
                    logger.info(f"     Document ID: {source.document_id}")
                    logger.info(f"     Section ID: {source.section_id}")
                    
                    # Show strategy metadata
                    metadata = source.metadata
                    logger.info(f"     Strategy Metadata:")
                    logger.info(f"       - Strategy: {metadata.get('strategy_used', 'N/A')}")
                    logger.info(f"       - Confidence: {metadata.get('strategy_confidence', 'N/A')}")
                    logger.info(f"       - Path Strength: {metadata.get('path_strength', 'N/A')}")
                    logger.info(f"       - Hop Count: {metadata.get('hop_count', 'N/A')}")
                    logger.info(f"       - Evidence Count: {metadata.get('evidence_count', 'N/A')}")
                    
                    if 'graph_path' in metadata:
                        logger.info(f"       - Graph Path: {' → '.join(metadata['graph_path'])}")
                    
                    if 'relationship_types' in metadata:
                        logger.info(f"       - Relationship Types: {metadata['relationship_types']}")
                    
                    # Show content preview
                    content_preview = source.content[:200] + "..." if len(source.content) > 200 else source.content
                    logger.info(f"     Content Preview: {content_preview}")
                    
            else:
                logger.warning("⚠️ No sources found for this query")
            
            # Step 4: Show graph paths if available
            if hasattr(response, 'graph_paths') and response.graph_paths:
                logger.info(f"\n🕸️ Graph Paths Found: {len(response.graph_paths)}")
                for j, path in enumerate(response.graph_paths, 1):
                    logger.info(f"  {j}. Path: {' → '.join(path.path)}")
                    logger.info(f"     Strength: {path.metadata.get('strength', 'N/A')}")
                    logger.info(f"     Hops: {path.metadata.get('hop_count', 'N/A')}")
            
            logger.info(f"\n✅ Query {i} completed successfully!")
            
        logger.info(f"\n{'='*80}")
        logger.info("🎉 ALL RETRIEVAL TESTS COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*80}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Retrieval service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_content():
    """Check what entities and relationships we have in the database"""
    logger.info("\n🔍 Checking database content...")
    
    try:
        db = await get_database()
        
        # Count entities
        entity_count = await db.entities.count_documents({})
        logger.info(f"📊 Total entities in database: {entity_count}")
        
        if entity_count > 0:
            logger.info("📋 Sample entities:")
            async for entity in db.entities.find().limit(5):
                logger.info(f"  - {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
        
        # Count relationships
        relationship_count = await db.relationships.count_documents({})
        logger.info(f"📊 Total relationships in database: {relationship_count}")
        
        if relationship_count > 0:
            logger.info("🔗 Sample relationships:")
            async for rel in db.relationships.find().limit(5):
                logger.info(f"  - {rel.get('source_entity', 'N/A')} → {rel.get('target_entity', 'N/A')} ({rel.get('relationship_type', 'N/A')})")
        
        return entity_count > 0 and relationship_count > 0
        
    except Exception as e:
        logger.error(f"❌ Database content check failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting GraphRAG Retrieval Service Test Suite")
    
    # First check if we have data in the database
    has_data = await test_database_content()
    
    if not has_data:
        logger.warning("⚠️ No entities or relationships found in database!")
        logger.info("Please run the pipeline test first to populate the database.")
        return False
    
    # Run retrieval tests
    success = await test_retrieval_service()
    
    if success:
        logger.info("\n🎉 All tests passed! Retrieval service is working correctly.")
    else:
        logger.error("\n❌ Some tests failed. Check the logs above for details.")
    
    return success

if __name__ == "__main__":
    # Run the retrieval service test
    success = asyncio.run(main())
    if success:
        print("\n✅ Retrieval service test completed successfully!")
    else:
        print("\n❌ Retrieval service test failed!")
