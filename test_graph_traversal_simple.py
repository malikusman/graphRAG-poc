#!/usr/bin/env python3
"""
Simple test for Graph Traversal Service

This test focuses on testing the core graph traversal functionality
without relying on document metadata that requires ObjectIds.
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
from app.services.graph_traversal_service import GraphTraversalService
from app.services.query_analysis_service import QueryAnalysisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_graph_traversal():
    """Test the graph traversal service directly"""
    logger.info("🚀 Starting Graph Traversal Service Test")
    
    try:
        # Get database connection
        db = await get_database()
        logger.info("✅ Database connection established")
        
        # Initialize services
        graph_traversal = GraphTraversalService(db)
        query_analyzer = QueryAnalysisService()
        logger.info("✅ Services initialized")
        
        # Test queries
        test_queries = [
            "What does CRISPR-Cas9 target?",
            "How does TP53 affect cancer?",
            "What are the relationships between CRISPR-Cas9 and TP53?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"🔍 TEST QUERY {i}: {query}")
            logger.info(f"{'='*80}")
            
            # Step 1: Analyze query
            logger.info("📊 Step 1: Analyzing query...")
            analysis = await query_analyzer.analyze_query(query)
            
            logger.info(f"Query Analysis:")
            logger.info(f"  Intent: {analysis.intent.value}")
            logger.info(f"  Complexity: {analysis.complexity.value}")
            logger.info(f"  Recommended Strategy: {analysis.recommended_strategy.value}")
            logger.info(f"  Entities Found: {len(analysis.entities)}")
            
            for j, entity in enumerate(analysis.entities, 1):
                logger.info(f"    {j}. {entity.name} ({entity.type}) - Confidence: {entity.confidence:.2f}")
            
            # Step 2: Find entities in knowledge graph
            logger.info("\n🔍 Step 2: Finding entities in knowledge graph...")
            entity_matches = await graph_traversal.find_entities_in_query(query, analysis)
            
            logger.info(f"Entity Matches Found: {len(entity_matches)}")
            for j, match in enumerate(entity_matches, 1):
                logger.info(f"  {j}. Query Entity: '{match.query_entity}'")
                logger.info(f"     Matched Entity: {match.matched_entity.entity_name} ({match.matched_entity.entity_type})")
                logger.info(f"     Match Type: {match.match_type}")
                logger.info(f"     Confidence: {match.confidence:.2f}")
                logger.info(f"     Reasoning: {match.reasoning}")
            
            # Step 3: Test graph traversal
            if entity_matches:
                logger.info("\n🕸️ Step 3: Testing graph traversal...")
                
                # Single entity exploration
                if len(entity_matches) == 1:
                    logger.info("Testing single entity exploration...")
                    entity = entity_matches[0].matched_entity
                    
                    paths = await graph_traversal.traverse_graph(
                        [entity],
                        max_hops=3,
                        min_strength=0.5,
                        max_paths=10
                    )
                    
                    logger.info(f"Found {len(paths)} paths from {entity.entity_name}")
                    
                    # Score paths
                    scored_paths = []
                    for path in paths:
                        score = graph_traversal.score_path(path)
                        scored_paths.append(score)
                    
                    # Sort by relevance
                    scored_paths.sort(key=lambda s: s.relevance_score, reverse=True)
                    
                    logger.info("Top paths:")
                    for j, score in enumerate(scored_paths[:5], 1):
                        logger.info(f"  {j}. Path: {' → '.join(score.path.path)}")
                        logger.info(f"     Relevance Score: {score.relevance_score:.3f}")
                        logger.info(f"     Path Strength: {score.path_strength:.3f}")
                        logger.info(f"     Hop Count: {score.hop_count}")
                        logger.info(f"     Evidence Count: {score.evidence_count}")
                        logger.info(f"     Relationship Types: {score.relationship_types}")
                
                # Entity pair path finding
                elif len(entity_matches) >= 2:
                    logger.info("Testing entity pair path finding...")
                    source_entity = entity_matches[0].matched_entity
                    target_entity = entity_matches[1].matched_entity
                    
                    paths = await graph_traversal.find_paths_between_entities(
                        [source_entity], [target_entity],
                        max_hops=3,
                        min_strength=0.5
                    )
                    
                    logger.info(f"Found {len(paths)} paths between {source_entity.entity_name} and {target_entity.entity_name}")
                    
                    # Score paths
                    scored_paths = []
                    for path in paths:
                        score = graph_traversal.score_path(path)
                        scored_paths.append(score)
                    
                    # Sort by relevance
                    scored_paths.sort(key=lambda s: s.relevance_score, reverse=True)
                    
                    logger.info("Top paths:")
                    for j, score in enumerate(scored_paths[:5], 1):
                        logger.info(f"  {j}. Path: {' → '.join(score.path.path)}")
                        logger.info(f"     Relevance Score: {score.relevance_score:.3f}")
                        logger.info(f"     Path Strength: {score.path_strength:.3f}")
                        logger.info(f"     Hop Count: {score.hop_count}")
                        logger.info(f"     Evidence Count: {score.evidence_count}")
                        logger.info(f"     Relationship Types: {score.relationship_types}")
                
            else:
                logger.warning("⚠️ No entities found in knowledge graph for this query")
            
            logger.info(f"\n✅ Query {i} completed successfully!")
        
        logger.info(f"\n{'='*80}")
        logger.info("🎉 ALL GRAPH TRAVERSAL TESTS COMPLETED SUCCESSFULLY!")
        logger.info(f"{'='*80}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Graph traversal test failed: {str(e)}")
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
    logger.info("🚀 Starting Graph Traversal Test Suite")
    
    # First check if we have data in the database
    has_data = await test_database_content()
    
    if not has_data:
        logger.warning("⚠️ No entities or relationships found in database!")
        logger.info("Please run the pipeline test first to populate the database.")
        return False
    
    # Run graph traversal tests
    success = await test_graph_traversal()
    
    if success:
        logger.info("\n🎉 All tests passed! Graph traversal is working correctly.")
    else:
        logger.error("\n❌ Some tests failed. Check the logs above for details.")
    
    return success

if __name__ == "__main__":
    # Run the graph traversal test
    success = asyncio.run(main())
    if success:
        print("\n✅ Graph traversal test completed successfully!")
    else:
        print("\n❌ Graph traversal test failed!")
