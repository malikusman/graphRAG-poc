#!/usr/bin/env python3
"""
Test GraphRAG pipeline with a small section and database storage (with fixed MongoDB URL)
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
from app.pipelines.graphrag_pipeline_enhanced import EnhancedGraphRAGPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def store_results_in_database(document_id: str, pipeline_result: dict):
    """Store the pipeline results in MongoDB"""
    logger.info(f"\n{'='*60}")
    logger.info(f"💾 STORING RESULTS IN DATABASE")
    logger.info(f"{'='*60}")
    
    try:
        # Get database connection
        db = await get_database()
        
        entities_stored = 0
        relationships_stored = 0
        
        # Store entities
        for entity_data in pipeline_result.get("final_entities", []):
            try:
                entity_doc = {
                    "entity_name": entity_data["entity_name"],
                    "entity_type": entity_data["entity_type"],
                    "entity_category": entity_data["entity_category"],
                    "entity_description": entity_data.get("description", entity_data.get("entity_description", "")),
                    "aliases": entity_data.get("aliases", []),
                    "frequency": entity_data.get("frequency", 1),
                    "paper_ids": [document_id],
                    "section_ids": entity_data.get("section_ids", []),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Upsert entity (update if exists, insert if not)
                result = await db.entities.update_one(
                    {
                        "entity_name": entity_doc["entity_name"],
                        "entity_type": entity_doc["entity_type"]
                    },
                    {"$set": entity_doc},
                    upsert=True
                )
                
                if result.upserted_id:
                    logger.info(f"✅ Stored new entity: {entity_doc['entity_name']} ({entity_doc['entity_type']})")
                else:
                    logger.info(f"🔄 Updated existing entity: {entity_doc['entity_name']} ({entity_doc['entity_type']})")
                
                entities_stored += 1
                
            except Exception as e:
                logger.error(f"❌ Error storing entity {entity_data.get('entity_name', 'unknown')}: {str(e)}")
        
        # Store relationships
        for rel_data in pipeline_result.get("final_relationships", []):
            try:
                rel_doc = {
                    "source_entity": rel_data["source_entity"],
                    "target_entity": rel_data["target_entity"],
                    "relationship_type": rel_data["relationship_type"],
                    "relationship_strength": rel_data["relationship_strength"],
                    "description": rel_data.get("description", ""),
                    "paper_ids": [document_id],
                    "section_ids": rel_data.get("section_ids", []),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Upsert relationship
                result = await db.relationships.update_one(
                    {
                        "source_entity": rel_doc["source_entity"],
                        "target_entity": rel_doc["target_entity"],
                        "relationship_type": rel_doc["relationship_type"]
                    },
                    {"$set": rel_doc},
                    upsert=True
                )
                
                if result.upserted_id:
                    logger.info(f"✅ Stored new relationship: {rel_doc['source_entity']} -> {rel_doc['target_entity']} ({rel_doc['relationship_type']})")
                else:
                    logger.info(f"🔄 Updated existing relationship: {rel_doc['source_entity']} -> {rel_doc['target_entity']} ({rel_doc['relationship_type']})")
                
                relationships_stored += 1
                
            except Exception as e:
                logger.error(f"❌ Error storing relationship {rel_data.get('source_entity', 'unknown')} -> {rel_data.get('target_entity', 'unknown')}: {str(e)}")
        
        logger.info(f"\n📊 STORAGE SUMMARY:")
        logger.info(f"  Entities stored: {entities_stored}")
        logger.info(f"  Relationships stored: {relationships_stored}")
        
        return {
            "entities_stored": entities_stored,
            "relationships_stored": relationships_stored
        }
        
    except Exception as e:
        logger.error(f"❌ Database storage failed: {str(e)}")
        raise

async def verify_database_storage(document_id: str):
    """Verify what was stored in the database"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🔍 VERIFYING DATABASE STORAGE")
    logger.info(f"{'='*60}")
    
    try:
        # Get database connection
        db = await get_database()
        
        # Check entities
        entities = []
        async for entity in db.entities.find({"paper_ids": document_id}):
            entities.append(entity)
        
        logger.info(f"📊 ENTITIES IN DATABASE: {len(entities)}")
        for i, entity in enumerate(entities, 1):
            logger.info(f"  {i}. {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
            logger.info(f"     Category: {entity.get('entity_category', 'N/A')}")
            logger.info(f"     Description: {entity.get('entity_description', 'N/A')[:100]}...")
            logger.info(f"     Frequency: {entity.get('frequency', 1)}")
            logger.info("")
        
        # Check relationships
        relationships = []
        async for rel in db.relationships.find({"paper_ids": document_id}):
            relationships.append(rel)
        
        logger.info(f"📊 RELATIONSHIPS IN DATABASE: {len(relationships)}")
        for i, rel in enumerate(relationships, 1):
            logger.info(f"  {i}. {rel.get('source_entity', 'N/A')} -> {rel.get('target_entity', 'N/A')}")
            logger.info(f"     Type: {rel.get('relationship_type', 'N/A')}")
            logger.info(f"     Strength: {rel.get('relationship_strength', 'N/A')}")
            logger.info(f"     Description: {rel.get('description', 'N/A')[:100]}...")
            logger.info("")
        
        logger.info(f"✅ Database verification complete!")
        return len(entities), len(relationships)
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {str(e)}")
        return 0, 0

async def test_small_section_fixed():
    """Test GraphRAG pipeline with a small section and database storage"""
    logger.info("🚀 Starting Small Section GraphRAG Test with Fixed Database Connection")
    
    try:
        # Create a small test document with one section
        document_id = "test_small_doc_002"
        sections = [
            {
                "_id": "section_small_002",
                "title": "Abstract",
                "text": "CRISPR-Cas9 is a revolutionary gene editing technology that allows precise modification of DNA sequences. This study demonstrates CRISPR-Cas9 targeting the TP53 gene in cancer cells, resulting in significant tumor suppression and enhanced apoptosis. The methodology achieved 90% editing efficiency using optimized guide RNAs. Results show that TP53 restoration leads to 50% reduction in cell proliferation and increased sensitivity to chemotherapy drugs like 5-fluorouracil.",
                "type": "abstract",
                "position": 1
            }
        ]
        
        logger.info(f"📄 Created test document with {len(sections)} section")
        logger.info(f"  Document ID: {document_id}")
        logger.info(f"  Section text length: {len(sections[0]['text'])} characters")
        
        # Initialize enhanced pipeline
        pipeline = EnhancedGraphRAGPipeline()
        logger.info("✅ Pipeline initialized successfully")
        
        # Process document through pipeline
        logger.info("\n🚀 Starting document processing...")
        start_time = datetime.now()
        result = await pipeline.process_document(document_id, sections)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Log pipeline results
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 PIPELINE PROCESSING COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"📊 PIPELINE RESULTS:")
        logger.info(f"  Document ID: {result.get('document_id', 'N/A')}")
        logger.info(f"  Success: {result.get('success', False)}")
        logger.info(f"  Entities Extracted: {result.get('entities_extracted', 0)}")
        logger.info(f"  Relationships Extracted: {result.get('relationships_extracted', 0)}")
        logger.info(f"  Final Entities: {len(result.get('final_entities', []))}")
        logger.info(f"  Final Relationships: {len(result.get('final_relationships', []))}")
        logger.info(f"  Processing Duration: {duration:.2f} seconds")
        
        if result.get('success'):
            # Store results in database
            storage_result = await store_results_in_database(document_id, result)
            
            # Verify database storage
            entities_count, relationships_count = await verify_database_storage(document_id)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🎉 TEST COMPLETED SUCCESSFULLY!")
            logger.info(f"{'='*60}")
            logger.info(f"📊 FINAL SUMMARY:")
            logger.info(f"  Entities processed: {len(result.get('final_entities', []))}")
            logger.info(f"  Relationships processed: {len(result.get('final_relationships', []))}")
            logger.info(f"  Entities in database: {entities_count}")
            logger.info(f"  Relationships in database: {relationships_count}")
            logger.info(f"  Total duration: {duration:.2f} seconds")
            
        else:
            logger.error(f"❌ Pipeline processing failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the small section test
    asyncio.run(test_small_section_fixed())

