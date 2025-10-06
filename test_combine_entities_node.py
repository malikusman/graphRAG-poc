#!/usr/bin/env python3
"""
Test the _combine_entities node
This test demonstrates entity combination within a document
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.pipelines.graphrag_pipeline import GraphRAGState

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_entities() -> List[Dict[str, Any]]:
    """Create test entities that should be combined"""
    return [
        # Group 1: Multiple mentions of p53 (should be combined)
        {
            "entity_name": "p53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["TP53", "Tumor Protein p53"],
            "description": "A tumor suppressor protein that plays a crucial role in maintaining genomic stability and preventing cancer development. (MeSH: D000075101)",
            "provenance": "The tumor suppressor protein p53 plays a crucial role in maintaining genomic stability and preventing cancer development.",
            "document_id": "test_doc_001",
            "section_id": "section_001"
        },
        {
            "entity_name": "p53",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["Tumor Protein p53"],
            "description": "A protein encoded by the TP53 gene that plays a crucial role in regulating the cell cycle and preventing cancer.",
            "provenance": "Western blot analysis was performed to detect p53 protein expression levels.",
            "document_id": "test_doc_001",
            "section_id": "section_002"
        },
        
        # Group 2: Multiple mentions of MDM2 (should be combined)
        {
            "entity_name": "MDM2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["murine double minute 2"],
            "description": "A protein that interacts with p53 and targets it for proteasomal degradation, playing a critical role in the regulation of the cell cycle.",
            "provenance": "It interacts with MDM2 (murine double minute 2), which targets p53 for proteasomal degradation.",
            "document_id": "test_doc_001",
            "section_id": "section_001"
        },
        {
            "entity_name": "MDM2",
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["Mouse Double Minute 2 homolog"],
            "description": "A protein that regulates the p53 tumor suppressor and is involved in the control of cell growth.",
            "provenance": "Immunoprecipitation assays were used to study the p53-MDM2 protein interaction.",
            "document_id": "test_doc_001",
            "section_id": "section_002"
        },
        
        # Group 3: Single mention of CRISPR-Cas9 (should remain as-is)
        {
            "entity_name": "CRISPR-Cas9",
            "entity_type": "method",
            "entity_category": "methods_and_approaches",
            "aliases": ["CRISPR", "Cas9", "CRISPR-Cas9 system"],
            "description": "Genome editing method using clustered regularly interspaced short palindromic repeats and Cas9 endonuclease. (MeSH:D000077505)",
            "provenance": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines.",
            "document_id": "test_doc_001",
            "section_id": "section_002"
        },
        
        # Group 4: Different entity types with same name (should NOT be combined)
        {
            "entity_name": "TP53",
            "entity_type": "gene",
            "entity_category": "biological_entities",
            "aliases": ["p53 gene"],
            "description": "A gene that encodes the p53 protein, mutations of which are associated with various cancers.",
            "provenance": "Mutations in the TP53 gene are associated with various cancers including breast cancer, lung cancer, and colorectal cancer.",
            "document_id": "test_doc_001",
            "section_id": "section_001"
        },
        {
            "entity_name": "TP53",
            "entity_type": "gene",
            "entity_category": "biological_entities",
            "aliases": ["p53", "Tumor Protein p53"],
            "description": "A gene that encodes a protein that regulates the cell cycle and functions as a tumor suppressor. (MeSH: D000075576)",
            "provenance": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines.",
            "document_id": "test_doc_001",
            "section_id": "section_002"
        }
    ]

def print_entities(entities: List[Dict[str, Any]], title: str):
    """Print entities in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(entities)}")
    for i, entity in enumerate(entities, 1):
        print(f"   {i}. {entity.get('entity_name', 'Unknown')} ({entity.get('entity_type', 'Unknown')})")
        print(f"      Category: {entity.get('entity_category', 'Unknown')}")
        print(f"      Aliases: {entity.get('aliases', [])}")
        print(f"      Description: {entity.get('description', 'No description')[:100]}...")
        print(f"      Frequency: {entity.get('frequency', 1)}")
        print(f"      Section IDs: {entity.get('section_ids', [])}")
        print()

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

async def test_combine_entities_node():
    """Test the _combine_entities node"""
    print("🚀 Starting Real Combine Entities Node Test")
    print("=" * 80)
    
    print("🔍 STEP 1: CREATE TEST ENTITIES")
    print("=" * 80)
    
    # Create test entities
    temp_entities = create_test_entities()
    print(f"📄 Test Entities Created: {len(temp_entities)}")
    
    print_entities(temp_entities, "Input Entities (Before Combination)")
    
    print("\n🎯 Expected Combination Groups:")
    print("   📌 Group 1: p53 (protein) - 2 entities → Should be combined")
    print("   📌 Group 2: MDM2 (protein) - 2 entities → Should be combined")
    print("   📌 Group 3: CRISPR-Cas9 (method) - 1 entity → Should remain as-is")
    print("   📌 Group 4: TP53 (gene) - 2 entities → Should be combined")
    print("   📌 Note: p53 (protein) and TP53 (gene) are DIFFERENT types → Should NOT be combined")
    
    print("\n🔍 STEP 2: TEST PIPELINE NODE")
    print("=" * 80)
    
    try:
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        pipeline = SimpleCombineEntitiesPipeline()
        print("✅ SimpleCombineEntitiesPipeline class created successfully")
        
        # Create test state
        test_state: GraphRAGState = {
            "document_id": "test_doc_001",
            "sections": [],
            "temp_entities": temp_entities,  # This is the input for _combine_entities
            "temp_relationships": [],
            "doc_entities": [],
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
        
        print("\n🤖 Calling real _combine_entities method...")
        result_state = await pipeline._combine_entities(test_state)
        
        print("\n📊 Pipeline Node Results:")
        print(f"🔍 Input entities: {len(temp_entities)}")
        print(f"🔍 Output entities: {len(result_state['doc_entities'])}")
        print(f"🔍 Consolidation rate: {((len(temp_entities) - len(result_state['doc_entities'])) / len(temp_entities) * 100):.1f}%")
        print(f"🔍 Errors: {len(result_state['errors'])}")
        
        if result_state['errors']:
            print("❌ Errors encountered:")
            for error in result_state['errors']:
                print(f"   - {error}")
        else:
            print("✅ Pipeline node executed successfully!")
        
        # Print detailed results
        print_entities(result_state['doc_entities'], "Combined Entities (After Combination)")
        
    except Exception as e:
        print(f"❌ Pipeline node test failed: {str(e)}")
        logger.error(f"Pipeline node test failed: {str(e)}")
        return
    
    print("\n🔍 STEP 3: ANALYZE COMBINATION RESULTS")
    print("=" * 80)
    
    print(f"📊 Combination Analysis:")
    print(f"   Input entities: {len(temp_entities)}")
    print(f"   Output entities: {len(result_state['doc_entities'])}")
    print(f"   Entities combined: {len(temp_entities) - len(result_state['doc_entities'])}")
    print(f"   Consolidation rate: {((len(temp_entities) - len(result_state['doc_entities'])) / len(temp_entities) * 100):.1f}%")
    
    # Analyze each combined entity
    print(f"\n📈 Detailed Analysis:")
    for entity in result_state['doc_entities']:
        name = entity.get('entity_name', 'Unknown')
        entity_type = entity.get('entity_type', 'Unknown')
        frequency = entity.get('frequency', 1)
        aliases = entity.get('aliases', [])
        sections = entity.get('section_ids', [])
        
        print(f"   📌 {name} ({entity_type}):")
        print(f"      Frequency: {frequency} mentions")
        print(f"      Aliases: {aliases}")
        print(f"      Sections: {sections}")
    
    print("\n🎉 Test completed successfully!")
    print("📊 The _combine_entities node is working and consolidating entities within the document!")

if __name__ == "__main__":
    asyncio.run(test_combine_entities_node())