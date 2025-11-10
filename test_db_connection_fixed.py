#!/usr/bin/env python3
"""
Test database connection with correct MongoDB URL (no auth)
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_database_connection_fixed():
    """Test database connection with correct MongoDB URL"""
    logger.info("🔍 Testing database connection with fixed URL...")
    
    try:
        # Use the correct MongoDB URL without authentication
        MONGODB_URL = "mongodb://localhost:27017/sagewrite"
        
        # Create MongoDB client
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.sagewrite
        
        # Test connection
        await client.admin.command('ping')
        logger.info("✅ Database connection successful!")
        
        # Test adding a random entity
        test_entity = {
            "entity_name": "Test Gene",
            "entity_type": "gene",
            "entity_category": "biological_entities",
            "entity_description": "A test gene for database connection testing",
            "aliases": ["test_gene", "TG"],
            "frequency": 1,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["test_section_001"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        logger.info("📝 Adding test entity...")
        result = await db.entities.insert_one(test_entity)
        logger.info(f"✅ Entity inserted with ID: {result.inserted_id}")
        
        # Test adding a random relationship
        test_relationship = {
            "source_entity": "Test Gene",
            "target_entity": "Test Protein",
            "relationship_type": "encodes",
            "relationship_strength": 0.8,
            "description": "Test gene encodes test protein",
            "paper_ids": ["test_doc_001"],
            "section_ids": ["test_section_001"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        logger.info("🔗 Adding test relationship...")
        result = await db.relationships.insert_one(test_relationship)
        logger.info(f"✅ Relationship inserted with ID: {result.inserted_id}")
        
        # Test reading the data back
        logger.info("📖 Reading data back from database...")
        
        # Count entities
        entity_count = await db.entities.count_documents({})
        logger.info(f"📊 Total entities in database: {entity_count}")
        
        # Count relationships
        relationship_count = await db.relationships.count_documents({})
        logger.info(f"📊 Total relationships in database: {relationship_count}")
        
        # Find our test entity
        test_entity_found = await db.entities.find_one({"entity_name": "Test Gene"})
        if test_entity_found:
            logger.info(f"✅ Found test entity: {test_entity_found['entity_name']} ({test_entity_found['entity_type']})")
        else:
            logger.error("❌ Test entity not found!")
        
        # Find our test relationship
        test_rel_found = await db.relationships.find_one({"source_entity": "Test Gene"})
        if test_rel_found:
            logger.info(f"✅ Found test relationship: {test_rel_found['source_entity']} -> {test_rel_found['target_entity']} ({test_rel_found['relationship_type']})")
        else:
            logger.error("❌ Test relationship not found!")
        
        # Close connection
        client.close()
        
        logger.info("🎉 Database connection test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the database connection test
    success = asyncio.run(test_database_connection_fixed())
    if success:
        print("\n✅ Database is working correctly!")
    else:
        print("\n❌ Database connection failed!")

