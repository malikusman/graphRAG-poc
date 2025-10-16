#!/usr/bin/env python3
"""
Test the _reduce_entities node and EntityCanonicalizer service
This test demonstrates entity canonicalization across documents
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.entities import Entity
from app.pipelines.graphrag_pipeline import GraphRAGState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_entities() -> List[Dict[str, Any]]:
    """Create test entities with potential duplicates and variations"""
    return [
        # Group 1: p53 variations (should be merged)
        {
            "entity_name": "p53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["TP53", "tumor protein p53"],
            "entity_description": "Tumor suppressor protein p53",
            "frequency": 3,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_001", "section_002", "section_003"]
        },
        {
            "entity_name": "TP53",
            "entity_type": "protein", 
            "entity_category": "biological_entities",
            "aliases": ["p53", "tumor protein p53"],
            "entity_description": "Tumor protein p53, a tumor suppressor",
            "frequency": 2,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_004", "section_005"]
        },
        {
            "entity_name": "tumor protein p53",
            "entity_type": "protein",
            "entity_category": "biological_entities", 
            "aliases": ["p53", "TP53"],
            "entity_description": "The p53 tumor suppressor protein",
            "frequency": 1,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_006"]
        },
        
        # Group 2: MDM2 variations (should be merged)
        {
            "entity_name": "MDM2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["murine double minute 2"],
            "entity_description": "MDM2 oncoprotein",
            "frequency": 2,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_007", "section_008"]
        },
        {
            "entity_name": "murine double minute 2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["MDM2"],
            "entity_description": "Murine double minute 2 protein",
            "frequency": 1,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_009"]
        },
        
        # Group 3: CRISPR variations (should be merged)
        {
            "entity_name": "CRISPR-Cas9",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["CRISPR", "Cas9"],
            "entity_description": "CRISPR-Cas9 gene editing system",
            "frequency": 2,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_010", "section_011"]
        },
        {
            "entity_name": "CRISPR",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["CRISPR-Cas9", "Cas9"],
            "entity_description": "CRISPR gene editing technology",
            "frequency": 1,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_012"]
        },
        
        # Group 4: Unique entities (should not be merged)
        {
            "entity_name": "apoptosis",
            "entity_type": "physiological_process",
            "entity_category": "physiological_processes",
            "aliases": ["programmed cell death"],
            "entity_description": "Programmed cell death process",
            "frequency": 1,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_013"]
        },
        {
            "entity_name": "cancer",
            "entity_type": "disease",
            "entity_category": "diseases_and_disorders",
            "aliases": ["tumor", "neoplasm"],
            "entity_description": "Cancer disease",
            "frequency": 1,
            "paper_ids": ["test_doc_001"],
            "section_ids": ["section_014"]
        }
    ]

def print_entities(entities: List[Dict[str, Any]], title: str):
    """Print entities in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(entities)}")
    for i, entity in enumerate(entities, 1):
        print(f"   {i}. {entity['entity_name']} ({entity['entity_type']})")
        print(f"      Category: {entity['entity_category']}")
        print(f"      Aliases: {entity.get('aliases', [])}")
        print(f"      Description: {entity['entity_description']}")
        print(f"      Frequency: {entity.get('frequency', 1)}")
        print(f"      Sections: {entity.get('section_ids', [])}")
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

async def test_real_reduce_entities():
    """Test the real _reduce_entities method"""
    print("🚀 Starting Real Reduce Entities Test")
    print("=" * 80)
    
    # Create test data
    test_entities = create_test_entities()
    print("📄 Test Data Created:")
    print(f"   📝 Input Entities: {len(test_entities)}")
    
    print_entities(test_entities, "Input Entities with Potential Duplicates")
    
    print("🔍 ENTITY CANONICALIZATION DEMONSTRATION")
    print("=" * 80)
    print("📝 Entity canonicalization merges similar entities by:")
    print("   1. Analyzing entity names, aliases, and descriptions")
    print("   2. Using LLM to determine semantic similarity")
    print("   3. Creating stable identifiers for merged entities")
    print("   4. Consolidating frequency and section information")
    
    print("\n🎯 Expected Merges:")
    print("   📌 Group 1: p53, TP53, tumor protein p53 → p53 (primary)")
    print("   📌 Group 2: MDM2, murine double minute 2 → MDM2 (primary)")
    print("   📌 Group 3: CRISPR-Cas9, CRISPR → CRISPR-Cas9 (primary)")
    print("   📌 Group 4: apoptosis, cancer → No merges (unique entities)")
    
    print("\n🧠 How LLM Canonicalizes Entities:")
    print("   1. Analyzes entity semantics and context")
    print("   2. Considers biological/biomedical knowledge")
    print("   3. Evaluates name similarity and alias overlap")
    print("   4. Determines primary entity name and stable identifiers")
    
    print("\n🛠️ CANONICALIZATION STRATEGIES")
    print("=" * 80)
    print("📝 The system uses different strategies for entity merging:")
    
    print("\n🎯 Strategy 1: Name-Based Merging")
    print("   When: Entity names are very similar")
    print("   Example: 'p53' vs 'TP53' → Choose 'p53' as primary")
    print("   Action: Merge entities with similar names")
    
    print("\n🎯 Strategy 2: Alias-Based Merging")
    print("   When: Entities share common aliases")
    print("   Example: Both 'p53' and 'TP53' have alias 'tumor protein p53'")
    print("   Action: Merge entities with overlapping aliases")
    
    print("\n🎯 Strategy 3: Description-Based Merging")
    print("   When: Entity descriptions are semantically similar")
    print("   Example: Both describe 'tumor suppressor protein'")
    print("   Action: Merge entities with similar descriptions")
    
    print("\n🎯 Strategy 4: Stable Identifier Matching")
    print("   When: Entities have matching stable identifiers")
    print("   Example: Both have UniProt ID 'P04637'")
    print("   Action: Merge entities with same stable identifiers")
    
    print("\n🎯 Strategy 5: LLM-Based Semantic Analysis")
    print("   When: Complex similarity analysis needed")
    print("   Example: 'CRISPR-Cas9' vs 'CRISPR' (part-whole relationship)")
    print("   Action: Use LLM to determine if entities should be merged")
    
    print("\n📋 CANONICALIZATION EXAMPLES FROM TEST DATA")
    print("=" * 80)
    
    print("🔍 Example 1: p53 Family")
    print("   Entity A: p53 (frequency: 3, aliases: ['TP53', 'tumor protein p53'])")
    print("   Entity B: TP53 (frequency: 2, aliases: ['p53', 'tumor protein p53'])")
    print("   Entity C: tumor protein p53 (frequency: 1, aliases: ['p53', 'TP53'])")
    print("   Canonicalization: Merge all three → p53 (primary)")
    print("   Result: p53 (frequency: 6, all aliases combined)")
    
    print("\n🔍 Example 2: MDM2 Family")
    print("   Entity A: MDM2 (frequency: 2, aliases: ['murine double minute 2'])")
    print("   Entity B: murine double minute 2 (frequency: 1, aliases: ['MDM2'])")
    print("   Canonicalization: Merge both → MDM2 (primary)")
    print("   Result: MDM2 (frequency: 3, all aliases combined)")
    
    print("\n🔍 Example 3: CRISPR Family")
    print("   Entity A: CRISPR-Cas9 (frequency: 2, aliases: ['CRISPR', 'Cas9'])")
    print("   Entity B: CRISPR (frequency: 1, aliases: ['CRISPR-Cas9', 'Cas9'])")
    print("   Canonicalization: Merge both → CRISPR-Cas9 (primary)")
    print("   Result: CRISPR-Cas9 (frequency: 3, all aliases combined)")
    
    print("\n🔍 STEP 1: CREATE SIMPLE PIPELINE CLASS")
    print("=" * 80)
    print("📝 Create a minimal pipeline class with just the _reduce_entities method")
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        pipeline = SimpleReduceEntitiesPipeline()
        print("✅ SimpleReduceEntitiesPipeline class created successfully")
        
    except Exception as e:
        print(f"❌ Error creating pipeline: {str(e)}")
        return
    
    print("\n🔍 STEP 2: TEST THE REAL METHOD")
    print("=" * 80)
    print("📝 Call the actual _reduce_entities method with our test data")
    
    try:
        # Create test state
        test_state: GraphRAGState = {
            "document_id": "test_doc_001",
            "sections": [],
            "temp_entities": [],
            "temp_relationships": [],
            "doc_entities": test_entities,
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
        print("✅ Pipeline instance created successfully")
        
        print("\n🤖 Calling real _reduce_entities method...")
        result_state = await pipeline._reduce_entities(test_state)
        
        print("\n📊 Real Pipeline Result:")
        print(f"🔍 Final Entities: {len(result_state['final_entities'])}")
        print(f"🔍 Merge Operations: {len(result_state['entity_merges'])}")
        print("✅ Real method call successful!")
        
        # Print detailed results
        print_entities(result_state['final_entities'], "Final Canonicalized Entities")
        print_merge_operations(result_state['entity_merges'])
        
    except Exception as e:
        print(f"❌ Real reduce entities test failed!")
        print(f"📊 Check the logs for error details.")
        logger.error(f"Real reduce entities test failed: {str(e)}")
        return
    
    print("\n🔍 STEP 3: ANALYZE THE RESULTS")
    print("=" * 80)
    print("📝 Analyze entity canonicalization results")
    
    print(f"📊 Results Analysis:")
    print(f"   Input entities: {len(test_entities)}")
    print(f"   Final entities: {len(result_state['final_entities'])}")
    print(f"   Merge operations: {len(result_state['entity_merges'])}")
    print(f"   Reduction rate: {((len(test_entities) - len(result_state['final_entities'])) / len(test_entities) * 100):.1f}%")
    
    print("\n🔍 STEP 4: TRY THE FULL PIPELINE CLASS")
    print("=" * 80)
    print("📝 Try to use the actual GraphRAGPipeline class")
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline
        print("✅ Full GraphRAGPipeline imported successfully")
        
        full_pipeline = GraphRAGPipeline()
        print("✅ Full pipeline instance created successfully")
        
        print("\n🤖 Calling full pipeline _reduce_entities method...")
        full_result_state = await full_pipeline._reduce_entities(test_state)
        
        print("\n📊 Full Pipeline Result:")
        print(f"🔍 Final Entities: {len(full_result_state['final_entities'])}")
        print(f"🔍 Merge Operations: {len(full_result_state['entity_merges'])}")
        print("✅ Full pipeline method call successful!")
        
        # Compare results
        if (len(result_state['final_entities']) == len(full_result_state['final_entities']) and
            len(result_state['entity_merges']) == len(full_result_state['entity_merges'])):
            print("🎉 Results match! Both methods found the same number of entities and merges.")
        else:
            print("⚠️ Results differ between simple and full pipeline methods.")
        
    except Exception as e:
        print(f"❌ Full pipeline test failed: {str(e)}")
        logger.error(f"Full pipeline test failed: {str(e)}")
    
    print("\n🎉 Real reduce entities test completed successfully!")
    print("📊 We successfully called the real _reduce_entities method!")

if __name__ == "__main__":
    asyncio.run(test_real_reduce_entities())
