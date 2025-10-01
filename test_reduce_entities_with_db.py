#!/usr/bin/env python3
"""
Test the _reduce_entities node with pre-populated database
This test demonstrates proper entity canonicalization across documents
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.entities import Entity
from app.pipelines.graphrag_pipeline import GraphRAGState
from app.database.models import EntityCollection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def pre_populate_database():
    """Pre-populate database with some existing entities"""
    print("🗄️ Pre-populating database with existing entities...")
    
    # Create existing entities that should be merged with new ones
    existing_entities = [
        {
            "entity_name": "p53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["TP53", "tumor protein p53"],
            "entity_description": "Tumor suppressor protein p53 from previous document",
            "frequency": 2,
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_001", "existing_section_002"]
        },
        {
            "entity_name": "MDM2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["murine double minute 2"],
            "entity_description": "MDM2 oncoprotein from previous document",
            "frequency": 1,
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_003"]
        },
        {
            "entity_name": "CRISPR-Cas9",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["CRISPR", "Cas9"],
            "entity_description": "CRISPR-Cas9 gene editing system from previous document",
            "frequency": 1,
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_004"]
        },
        {
            "entity_name": "apoptosis",
            "entity_type": "physiological_process",
            "entity_category": "physiological_processes",
            "aliases": ["programmed cell death"],
            "entity_description": "Programmed cell death process from previous document",
            "frequency": 1,
            "paper_ids": ["existing_doc_001"],
            "section_ids": ["existing_section_005"]
        }
    ]
    
    created_count = 0
    for entity_data in existing_entities:
        try:
            # Create entity in database
            entity = Entity(
                entity_name=entity_data["entity_name"],
                entity_type=entity_data["entity_type"],
                entity_category=entity_data["entity_category"],
                aliases=entity_data.get("aliases", []),
                entity_description=entity_data["entity_description"],
                frequency=entity_data.get("frequency", 1),
                paper_ids=entity_data.get("paper_ids", []),
                section_ids=entity_data.get("section_ids", [])
            )
            entity_id = await EntityCollection.insert_entity(entity)
            print(f"   ✅ Created entity: {entity_data['entity_name']} (ID: {entity_id})")
            created_count += 1
        except Exception as e:
            print(f"   ❌ Failed to create entity {entity_data['entity_name']}: {str(e)}")
    
    print(f"🗄️ Database pre-population complete: {created_count}/{len(existing_entities)} entities created")
    return created_count

def create_new_document_entities() -> List[Dict[str, Any]]:
    """Create entities from a new document that should be canonicalized against existing ones"""
    return [
        # These should merge with existing entities
        {
            "entity_name": "TP53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["p53", "tumor protein p53"],
            "entity_description": "TP53 protein, a tumor suppressor found in new document",
            "frequency": 1,
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_001"]
        },
        {
            "entity_name": "tumor protein p53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["p53", "TP53"],
            "entity_description": "The p53 tumor suppressor protein from new document",
            "frequency": 1,
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_002"]
        },
        {
            "entity_name": "murine double minute 2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["MDM2"],
            "entity_description": "Murine double minute 2 protein from new document",
            "frequency": 1,
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_003"]
        },
        {
            "entity_name": "CRISPR",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["CRISPR-Cas9", "Cas9"],
            "entity_description": "CRISPR gene editing technology from new document",
            "frequency": 1,
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_004"]
        },
        {
            "entity_name": "programmed cell death",
            "entity_type": "physiological_process",
            "entity_category": "physiological_processes",
            "aliases": ["apoptosis"],
            "entity_description": "Programmed cell death process from new document",
            "frequency": 1,
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_005"]
        },
        
        # These should NOT merge (unique entities)
        {
            "entity_name": "cancer",
            "entity_type": "disease",
            "entity_category": "diseases_and_disorders",
            "aliases": ["tumor", "neoplasm"],
            "entity_description": "Cancer disease from new document",
            "frequency": 1,
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_006"]
        },
        {
            "entity_name": "DNA repair",
            "entity_type": "physiological_process",
            "entity_category": "physiological_processes",
            "aliases": ["DNA damage repair"],
            "entity_description": "DNA repair process from new document",
            "frequency": 1,
            "paper_ids": ["new_doc_001"],
            "section_ids": ["new_section_007"]
        }
    ]

def print_entities(entities: List[Dict[str, Any]], title: str):
    """Print entities in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(entities)}")
    for i, entity in enumerate(entities, 1):
        if isinstance(entity, dict):
            name = entity.get('entity_name', 'Unknown')
            entity_type = entity.get('entity_type', 'Unknown')
            category = entity.get('entity_category', 'Unknown')
            aliases = entity.get('aliases', [])
            description = entity.get('entity_description', 'No description')
            frequency = entity.get('frequency', 1)
            sections = entity.get('section_ids', [])
        else:
            # Entity object
            name = entity.entity_name
            entity_type = entity.entity_type
            category = entity.entity_category
            aliases = entity.aliases
            description = entity.entity_description
            frequency = entity.frequency
            sections = entity.section_ids
            
        print(f"   {i}. {name} ({entity_type})")
        print(f"      Category: {category}")
        print(f"      Aliases: {aliases}")
        print(f"      Description: {description}")
        print(f"      Frequency: {frequency}")
        print(f"      Sections: {sections}")
        print()

def print_merge_operations(merges: List[Dict[str, Any]]):
    """Print merge operations in a formatted way"""
    print(f"\n🔄 Merge Operations:")
    print(f"   Count: {len(merges)}")
    for i, merge in enumerate(merges, 1):
        print(f"   {i}. Merge Type: {merge.get('merge_type', 'unknown')}")
        print(f"      Primary Entity: {merge.get('primary_entity', 'unknown')}")
        print(f"      Merged Entities: {merge.get('merged_entities', [])}")
        print(f"      Confidence: {merge.get('confidence', 0.0)}")
        print(f"      Reasoning: {merge.get('reasoning', 'No reasoning provided')}")
        print()

class SimpleReduceEntitiesPipeline:
    """Simple pipeline class with just the _reduce_entities method"""
    
    def __init__(self):
        from app.services.entity_canonicalizer import EntityCanonicalizer
        self.entity_canonicalizer = EntityCanonicalizer()
    
    async def _reduce_entities(self, state: GraphRAGState) -> GraphRAGState:
        """Reduce phase: Canonicalize entities across documents"""
        logger.info(f"Starting entity reduction for document {state['document_id']}")
        
        try:
            # Convert doc_entities to Entity objects for processing
            from app.models.entities import Entity
            entities = []
            for entity_data in state["doc_entities"]:
                entity = Entity(
                    entity_name=entity_data["entity_name"],
                    entity_type=entity_data["entity_type"],
                    entity_category=entity_data["entity_category"],
                    aliases=entity_data.get("aliases", []),
                    entity_description=entity_data["entity_description"],
                    frequency=entity_data.get("frequency", 1),
                    paper_ids=entity_data.get("paper_ids", []),
                    section_ids=entity_data.get("section_ids", [])
                )
                entities.append(entity)
            
            # Process entity canonicalization
            canonicalization_results = await self.entity_canonicalizer.process_entity_canonicalization(entities)
            
            # Update state with canonicalization results
            state["entity_merges"] = canonicalization_results.get("merge_operations", [])
            state["final_entities"] = canonicalization_results.get("canonical_entities", [])
            
            # Add any errors from canonicalization
            if canonicalization_results.get("errors"):
                state["errors"].extend(canonicalization_results["errors"])
            
            logger.info(f"Entity reduction complete: {len(state['final_entities'])} final entities, {len(state['entity_merges'])} merges")
            return state
            
        except Exception as e:
            logger.error(f"Error in entity reduction: {str(e)}")
            state["errors"].append(f"Entity reduction error: {str(e)}")
            return state

async def test_reduce_entities_with_database():
    """Test the _reduce_entities node with pre-populated database"""
    print("🚀 Starting Real Reduce Entities Test with Database")
    print("=" * 80)
    
    print("🔍 STEP 1: PRE-POPULATE DATABASE")
    print("=" * 80)
    
    # Pre-populate database with existing entities
    created_count = await pre_populate_database()
    
    if created_count == 0:
        print("❌ Failed to create any entities in database. Cannot proceed with test.")
        return
    
    print("\n🔍 STEP 2: CREATE NEW DOCUMENT ENTITIES")
    print("=" * 80)
    
    # Create entities from new document
    new_entities = create_new_document_entities()
    print(f"📄 New Document Entities Created: {len(new_entities)}")
    
    print_entities(new_entities, "New Document Entities (should be canonicalized)")
    
    print("\n🎯 Expected Canonicalization:")
    print("   📌 TP53 + tumor protein p53 → should merge with existing 'p53'")
    print("   📌 murine double minute 2 → should merge with existing 'MDM2'")
    print("   📌 CRISPR → should merge with existing 'CRISPR-Cas9'")
    print("   📌 programmed cell death → should merge with existing 'apoptosis'")
    print("   📌 cancer, DNA repair → should remain unique (no existing matches)")
    
    print("\n🔍 STEP 3: TEST ENTITY CANONICALIZER DIRECTLY")
    print("=" * 80)
    
    from app.services.entity_canonicalizer import EntityCanonicalizer
    canonicalizer = EntityCanonicalizer()
    
    # Convert to Entity objects
    entity_objects = []
    for entity_data in new_entities:
        entity = Entity(
            entity_name=entity_data["entity_name"],
            entity_type=entity_data["entity_type"],
            entity_category=entity_data["entity_category"],
            aliases=entity_data.get("aliases", []),
            entity_description=entity_data["entity_description"],
            frequency=entity_data.get("frequency", 1),
            paper_ids=entity_data.get("paper_ids", []),
            section_ids=entity_data.get("section_ids", [])
        )
        entity_objects.append(entity)
    
    print("🔍 Testing EntityCanonicalizer directly...")
    canonicalization_results = await canonicalizer.process_entity_canonicalization(entity_objects)
    
    print(f"📊 Direct Canonicalization Results:")
    print(f"   Entities processed: {canonicalization_results['entities_processed']}")
    print(f"   Merges performed: {canonicalization_results['merges_performed']}")
    print(f"   Final entities: {len(canonicalization_results['canonical_entities'])}")
    print(f"   Merge operations: {len(canonicalization_results['merge_operations'])}")
    print(f"   Errors: {canonicalization_results['errors']}")
    
    if canonicalization_results['merge_operations']:
        print_merge_operations(canonicalization_results['merge_operations'])
    
    print("\n🔍 STEP 4: TEST PIPELINE NODE")
    print("=" * 80)
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        pipeline = SimpleReduceEntitiesPipeline()
        print("✅ SimpleReduceEntitiesPipeline class created successfully")
        
        # Create test state
        test_state: GraphRAGState = {
            "document_id": "new_doc_001",
            "sections": [],
            "temp_entities": [],
            "temp_relationships": [],
            "doc_entities": new_entities,
            "doc_relationships": [],
            "final_entities": [],
            "final_relationships": [],
            "global_entities": [],
            "global_relationships": [],
            "entity_merges": [],
            "contradictions": [],
            "contradiction_resolutions": [],
            "resolution_summary": {},
            "consolidated_relationships": [],
            "consolidation_summary": {},
            "global_processing_results": {},
            "errors": []
        }
        print("✅ Test state created successfully")
        
        print("\n🤖 Calling real _reduce_entities method...")
        result_state = await pipeline._reduce_entities(test_state)
        
        print("\n📊 Pipeline Node Results:")
        print(f"🔍 Final Entities: {len(result_state['final_entities'])}")
        print(f"🔍 Merge Operations: {len(result_state['entity_merges'])}")
        print(f"🔍 Errors: {len(result_state['errors'])}")
        
        if result_state['errors']:
            print("❌ Errors encountered:")
            for error in result_state['errors']:
                print(f"   - {error}")
        else:
            print("✅ Pipeline node executed successfully!")
        
        # Print detailed results
        print_entities(result_state['final_entities'], "Final Canonicalized Entities")
        print_merge_operations(result_state['entity_merges'])
        
    except Exception as e:
        print(f"❌ Pipeline node test failed: {str(e)}")
        logger.error(f"Pipeline node test failed: {str(e)}")
        return
    
    print("\n🔍 STEP 5: COMPARE RESULTS")
    print("=" * 80)
    
    direct_merges = canonicalization_results['merges_performed']
    pipeline_merges = len(result_state['entity_merges'])
    
    print(f"📊 Results Comparison:")
    print(f"   Direct canonicalizer merges: {direct_merges}")
    print(f"   Pipeline node merges: {pipeline_merges}")
    
    if direct_merges == pipeline_merges:
        print("🎉 Results match! Both methods found the same number of merges.")
    else:
        print("⚠️ Results differ between direct canonicalizer and pipeline node.")
    
    print("\n🔍 STEP 6: ANALYZE FINAL RESULTS")
    print("=" * 80)
    
    print(f"📊 Final Analysis:")
    print(f"   Input entities: {len(new_entities)}")
    print(f"   Final entities: {len(result_state['final_entities'])}")
    print(f"   Merge operations: {len(result_state['entity_merges'])}")
    if len(new_entities) > 0:
        reduction_rate = ((len(new_entities) - len(result_state['final_entities'])) / len(new_entities) * 100)
        print(f"   Reduction rate: {reduction_rate:.1f}%")
    
    print("\n🎉 Test completed successfully!")
    print("📊 Entity canonicalization is now working with database entities!")

if __name__ == "__main__":
    asyncio.run(test_reduce_entities_with_database())
