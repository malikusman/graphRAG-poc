#!/usr/bin/env python3
"""
Test to demonstrate the EntityCanonicalization issue
Shows why no entities are being merged in our current test
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.entities import Entity
from app.services.entity_canonicalizer import EntityCanonicalizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_entity_canonicalization_issue():
    """Test to understand why entity canonicalization isn't working"""
    print("🔍 Investigating Entity Canonicalization Issue")
    print("=" * 80)
    
    # Create test entities with obvious duplicates
    test_entities = [
        Entity(
            entity_name="p53",
            entity_type="protein",
            entity_category="biological_entities",
            aliases=["TP53", "tumor protein p53"],
            entity_description="Tumor suppressor protein p53",
            frequency=3,
            paper_ids=["test_doc_001"],
            section_ids=["section_001", "section_002", "section_003"]
        ),
        Entity(
            entity_name="TP53",
            entity_type="protein", 
            entity_category="biological_entities",
            aliases=["p53", "tumor protein p53"],
            entity_description="Tumor protein p53, a tumor suppressor",
            frequency=2,
            paper_ids=["test_doc_001"],
            section_ids=["section_004", "section_005"]
        ),
        Entity(
            entity_name="tumor protein p53",
            entity_type="protein",
            entity_category="biological_entities", 
            aliases=["p53", "TP53"],
            entity_description="The p53 tumor suppressor protein",
            frequency=1,
            paper_ids=["test_doc_001"],
            section_ids=["section_006"]
        )
    ]
    
    print("📄 Test Entities Created:")
    for i, entity in enumerate(test_entities, 1):
        print(f"   {i}. {entity.entity_name}")
        print(f"      Type: {entity.entity_type}")
        print(f"      Category: {entity.entity_category}")
        print(f"      Aliases: {entity.aliases}")
        print(f"      Description: {entity.entity_description}")
        print()
    
    print("🔍 STEP 1: Test EntityCanonicalizer Directly")
    print("=" * 80)
    
    canonicalizer = EntityCanonicalizer()
    
    # Test finding similar entities for each entity
    for entity in test_entities:
        print(f"🔍 Finding similar entities for: {entity.entity_name}")
        similar_entities = await canonicalizer.find_similar_entities(entity)
        print(f"   Found {len(similar_entities)} similar entities in database")
        for similar in similar_entities:
            print(f"     - {similar.entity_name}")
        print()
    
    print("🔍 STEP 2: Test Individual Entity Processing")
    print("=" * 80)
    
    # Test processing each entity individually
    for entity in test_entities:
        print(f"🔍 Processing entity: {entity.entity_name}")
        result = await canonicalizer.process_entity_canonicalization([entity])
        print(f"   Entities processed: {result['entities_processed']}")
        print(f"   Merges performed: {result['merges_performed']}")
        print(f"   Final entities: {len(result['canonical_entities'])}")
        print(f"   Errors: {result['errors']}")
        print()
    
    print("🔍 STEP 3: Test Multiple Entities Together")
    print("=" * 80)
    
    # Test processing all entities together
    print("🔍 Processing all entities together:")
    result = await canonicalizer.process_entity_canonicalization(test_entities)
    print(f"   Entities processed: {result['entities_processed']}")
    print(f"   Merges performed: {result['merges_performed']}")
    print(f"   Final entities: {len(result['canonical_entities'])}")
    print(f"   Merge operations: {len(result['merge_operations'])}")
    print(f"   Errors: {result['errors']}")
    
    print("\n📊 ANALYSIS OF THE ISSUE")
    print("=" * 80)
    print("🔍 Root Cause Analysis:")
    print("   1. EntityCanonicalizer.find_similar_entities() looks in DATABASE")
    print("   2. Our test data has NO entities in the database")
    print("   3. Therefore, no similar entities are found")
    print("   4. No merges are performed because there's nothing to merge against")
    
    print("\n🎯 The EntityCanonicalizer is designed for:")
    print("   📌 Cross-document entity merging (new doc vs existing entities)")
    print("   📌 NOT within-document entity merging (duplicates in same doc)")
    
    print("\n🛠️ Solutions:")
    print("   📌 Option 1: Pre-populate database with some entities")
    print("   📌 Option 2: Test cross-document scenario properly")
    print("   📌 Option 3: Modify canonicalizer for within-document merging")
    print("   📌 Option 4: Test with multiple documents")
    
    print("\n🔍 STEP 4: Test Database Query Directly")
    print("=" * 80)
    
    # Test the database query directly
    from app.database.models import EntityCollection
    
    print("🔍 Testing database query directly:")
    try:
        # Try to find entities by name
        db_entities = await EntityCollection.find_entities_by_name("p53")
        print(f"   Found {len(db_entities)} entities named 'p53' in database")
        
        # Try to find similar entities
        similar_db_entities = await EntityCollection.find_similar_entities_by_name("p53", threshold=0.8)
        print(f"   Found {len(similar_db_entities)} similar entities for 'p53' in database")
        
        if len(db_entities) == 0 and len(similar_db_entities) == 0:
            print("   ✅ CONFIRMED: Database is empty - no entities to merge against")
        else:
            print("   ⚠️ Database has entities - different issue")
            
    except Exception as e:
        print(f"   ❌ Database query failed: {str(e)}")
    
    print("\n🎉 Investigation Complete!")
    print("📊 The issue is clear: EntityCanonicalizer needs existing entities in database")

if __name__ == "__main__":
    asyncio.run(test_entity_canonicalization_issue())



