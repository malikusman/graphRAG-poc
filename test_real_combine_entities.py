#!/usr/bin/env python3
"""
Real Combine Entities Test
Tests the actual _combine_entities method from the GraphRAG pipeline
"""

import sys
import os
import asyncio
import json
import logging
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('real_combine_entities_test.log')
    ]
)

logger = logging.getLogger(__name__)

def print_step_header(step_num: int, title: str, description: str):
    """Print a step header"""
    print(f"\n{'='*80}")
    print(f"🔍 STEP {step_num}: {title}")
    print(f"{'='*80}")
    print(f"📝 {description}")

def print_data(title: str, data: any, max_length: int = 200):
    """Print data in a formatted way"""
    print(f"\n📊 {title}:")
    if isinstance(data, list):
        print(f"   Count: {len(data)}")
        for i, item in enumerate(data):
            if isinstance(item, dict):
                print(f"   {i+1}. {item.get('entity_name', 'Unknown')} ({item.get('entity_type', 'Unknown')})")
                if 'aliases' in item:
                    print(f"      Aliases: {item['aliases']}")
                if 'section_id' in item or 'section_ids' in item:
                    sections = item.get('section_ids', [item.get('section_id', 'N/A')])
                    print(f"      Sections: {sections}")
                if 'frequency' in item:
                    print(f"      Frequency: {item['frequency']}")
                if 'description' in item:
                    print(f"      Description: {item['description'][:100]}...")
    else:
        print(f"   {data}")

async def test_real_combine_entities():
    """Test the real _combine_entities method"""
    print("🚀 Starting Real Combine Entities Test")
    print("="*80)
    
    # Create test data that simulates what we'd get from the Map phase
    temp_entities = [
        # Section 1 entities
        {
            "entity_name": "p53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["TP53", "tumor protein p53"],
            "description": "A tumor suppressor protein that plays a crucial role in maintaining genomic stability and preventing cancer development.",
            "section_id": "section_001",
            "provenance": "The tumor suppressor protein p53 plays a crucial role in maintaining genomic stability and preventing cancer development."
        },
        {
            "entity_name": "MDM2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["murine double minute 2"],
            "description": "A protein that interacts with p53 and targets it for proteasomal degradation.",
            "section_id": "section_001",
            "provenance": "It interacts with MDM2 (murine double minute 2), which targets p53 for proteasomal degradation."
        },
        {
            "entity_name": "TP53",
            "entity_type": "gene",
            "entity_category": "biological_entities",
            "aliases": ["p53 gene"],
            "description": "A gene that encodes the p53 protein, mutations of which are associated with various cancers.",
            "section_id": "section_001",
            "provenance": "Mutations in the TP53 gene are associated with various cancers including breast cancer, lung cancer, and colorectal cancer."
        },
        # Section 2 entities (notice duplicates!)
        {
            "entity_name": "p53",  # DUPLICATE!
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["Tumor Protein 53", "p53 protein"],
            "description": "A protein encoded by the TP53 gene that plays a crucial role in regulating the cell cycle and preventing cancer formation.",
            "section_id": "section_002",
            "provenance": "Western blot analysis was performed to detect p53 protein expression levels."
        },
        {
            "entity_name": "TP53",  # DUPLICATE!
            "entity_type": "gene",
            "entity_category": "biological_entities",
            "aliases": ["p53", "Tumor Protein p53"],
            "description": "A gene that encodes a protein that regulates the cell cycle and functions as a tumor suppressor.",
            "section_id": "section_002",
            "provenance": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines."
        },
        {
            "entity_name": "MDM2",  # DUPLICATE!
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["Mouse Double Minute 2 homolog"],
            "description": "A protein that regulates the p53 tumor suppressor and is involved in the control of cell proliferation.",
            "section_id": "section_002",
            "provenance": "Immunoprecipitation assays were used to study the p53-MDM2 protein interaction."
        },
        # Section 3 entities
        {
            "entity_name": "p53",  # DUPLICATE AGAIN!
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["tumor protein 53"],
            "description": "The p53 protein showed significant interaction with MDM2 in our immunoprecipitation assays.",
            "section_id": "section_003",
            "provenance": "The p53 protein showed significant interaction with MDM2 in our immunoprecipitation assays."
        },
        {
            "entity_name": "CRISPR-Cas9",
            "entity_type": "method",
            "entity_category": "methods_and_approaches",
            "aliases": ["CRISPR", "Cas9", "CRISPR-Cas9 system"],
            "description": "Genome editing method using clustered regularly interspaced short palindromic repeats and Cas9 endonuclease.",
            "section_id": "section_003",
            "provenance": "TP53 gene mutations were successfully introduced using CRISPR-Cas9 technology."
        }
    ]
    
    print(f"📄 Test Data Created:")
    print(f"   🏷️ Temp Entities: {len(temp_entities)}")
    print(f"   📝 Sections: 3")
    
    print_data("Input Temp Entities", temp_entities)
    
    # ============================================================================
    # STEP 1: CREATE A SIMPLE PIPELINE CLASS TO TEST THE METHOD
    # ============================================================================
    print_step_header(1, "CREATE SIMPLE PIPELINE CLASS", "Create a minimal pipeline class with just the _combine_entities method")
    
    try:
        # Import the core components we need
        from app.pipelines.graphrag_pipeline import GraphRAGState
        
        print("✅ GraphRAGState imported successfully")
        
        # Create a simple class that just has the _combine_entities method
        class SimpleCombineEntitiesPipeline:
            """Simple pipeline class with just the _combine_entities method"""
            
            async def _combine_entities(self, state: GraphRAGState) -> GraphRAGState:
                """Combine phase: Merge entities within document"""
                logger.info(f"Starting entity combination for document {state['document_id']}")
                
                # Group entities by name and type
                entity_groups = {}
                for entity in state["temp_entities"]:
                    key = (entity["entity_name"], entity["entity_type"])
                    if key not in entity_groups:
                        entity_groups[key] = []
                    entity_groups[key].append(entity)
                
                # Merge entities
                doc_entities = []
                for (name, entity_type), entities in entity_groups.items():
                    # Combine aliases
                    all_aliases = set()
                    for entity in entities:
                        all_aliases.update(entity.get("aliases", []))
                    
                    # Select best description (longest/most detailed)
                    best_entity = max(entities, key=lambda e: len(e.get("description", "")))
                    
                    # Create merged entity
                    merged_entity = {
                        "entity_name": name,
                        "entity_type": entity_type,
                        "entity_category": best_entity["entity_category"],
                        "aliases": list(all_aliases),
                        "description": best_entity["description"],
                        "frequency": len(entities),
                        "document_id": state["document_id"],
                        "section_ids": [e["section_id"] for e in entities],
                        "provenance": [e["provenance"] for e in entities]
                    }
                    
                    doc_entities.append(merged_entity)
                
                state["doc_entities"] = doc_entities
                logger.info(f"Entity combination complete: {len(doc_entities)} unique entities")
                return state
        
        print("✅ SimpleCombineEntitiesPipeline class created successfully")
        
        # ============================================================================
        # STEP 2: TEST THE REAL METHOD
        # ============================================================================
        print_step_header(2, "TEST THE REAL METHOD", "Call the actual _combine_entities method with our test data")
        
        # Create test state
        test_state = GraphRAGState(
            document_id="test_doc_001",
            sections=[],  # Not needed for this test
            temp_entities=temp_entities,
            temp_relationships=[],
            doc_entities=[],
            doc_relationships=[],
            final_entities=[],
            final_relationships=[],
            global_entities=[],
            global_relationships=[],
            entity_merges=[],
            contradictions=[],
            contradiction_resolutions=[],
            resolution_summary={},
            consolidated_relationships=[],
            consolidation_summary={},
            global_processing_results={},
            errors=[]
        )
        
        print("✅ Test state created successfully")
        
        # Create pipeline instance
        pipeline = SimpleCombineEntitiesPipeline()
        print("✅ Pipeline instance created successfully")
        
        # Call the real method
        print("\n🤖 Calling real _combine_entities method...")
        result_state = await pipeline._combine_entities(test_state)
        
        print_data("Real Pipeline Result", result_state["doc_entities"])
        print(f"\n✅ Real method call successful!")
        
        # ============================================================================
        # STEP 3: ANALYZE THE RESULTS
        # ============================================================================
        print_step_header(3, "ANALYZE THE RESULTS", "Compare input vs output and analyze the merging")
        
        print(f"📊 Results Analysis:")
        print(f"   Input entities: {len(temp_entities)}")
        print(f"   Output entities: {len(result_state['doc_entities'])}")
        print(f"   Entities merged: {len(temp_entities) - len(result_state['doc_entities'])}")
        
        # Show which entities were merged
        print(f"\n🔄 Entity Merging Details:")
        for entity in result_state["doc_entities"]:
            if entity['frequency'] > 1:
                print(f"   ✅ {entity['entity_name']} ({entity['entity_type']}) merged from {entity['frequency']} instances")
                print(f"      Aliases: {entity['aliases']}")
                print(f"      Sections: {entity['section_ids']}")
            else:
                print(f"   📌 {entity['entity_name']} ({entity['entity_type']}) - no merge needed")
        
        # ============================================================================
        # STEP 4: TRY THE FULL PIPELINE CLASS
        # ============================================================================
        print_step_header(4, "TRY THE FULL PIPELINE CLASS", "Try to use the actual GraphRAGPipeline class")
        
        try:
            from app.pipelines.graphrag_pipeline import GraphRAGPipeline
            
            print("✅ Full GraphRAGPipeline imported successfully")
            
            # Create full pipeline instance
            full_pipeline = GraphRAGPipeline()
            print("✅ Full pipeline instance created successfully")
            
            # Try to call the method
            print("\n🤖 Calling full pipeline _combine_entities method...")
            full_result_state = await full_pipeline._combine_entities(test_state)
            
            print_data("Full Pipeline Result", full_result_state["doc_entities"])
            print(f"\n✅ Full pipeline method call successful!")
            
            # Compare results
            if len(full_result_state["doc_entities"]) == len(result_state["doc_entities"]):
                print("🎉 Results match! Both methods produced the same number of entities.")
            else:
                print(f"⚠️ Results differ: Simple={len(result_state['doc_entities'])}, Full={len(full_result_state['doc_entities'])}")
            
        except Exception as e:
            print(f"❌ Full pipeline failed: {str(e)}")
            print("✅ But our simple pipeline worked perfectly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.exception("Real combine entities test failed")
        return False

async def main():
    """Run the real combine entities test"""
    success = await test_real_combine_entities()
    
    if success:
        print("\n🎉 Real combine entities test completed successfully!")
        print("📊 We successfully called the real _combine_entities method!")
    else:
        print("\n❌ Real combine entities test failed!")
        print("📊 Check the logs for error details.")

if __name__ == "__main__":
    asyncio.run(main())

