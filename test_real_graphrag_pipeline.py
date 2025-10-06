#!/usr/bin/env python3
"""
Real GraphRAG Pipeline Test
Tests the complete GraphRAG pipeline with real services and detailed explanations
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
        logging.FileHandler('real_graphrag_pipeline_test.log')
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
                print(f"   {i+1}. {item.get('entity_name', item.get('source_entity', 'Unknown'))} -> {item.get('target_entity', 'N/A')}")
                for key, value in item.items():
                    if key not in ['entity_name', 'source_entity', 'target_entity']:
                        if isinstance(value, str) and len(value) > max_length:
                            print(f"      {key}: {value[:max_length]}...")
                        else:
                            print(f"      {key}: {value}")
            else:
                print(f"   {i+1}. {item}")
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_length:
                print(f"   {key}: {value[:max_length]}...")
            else:
                print(f"   {key}: {value}")
    else:
        print(f"   {data}")

def print_explanation(title: str, explanation: str):
    """Print a detailed explanation"""
    print(f"\n📚 {title}:")
    print(f"   {explanation}")

def print_service_info(service_name: str, service_instance: any):
    """Print information about a service"""
    print(f"\n🔧 {service_name} Service:")
    print(f"   Type: {type(service_instance).__name__}")
    print(f"   Module: {type(service_instance).__module__}")
    print(f"   Methods: {[method for method in dir(service_instance) if not method.startswith('_')]}")

async def test_real_graphrag_pipeline():
    """Test the complete GraphRAG pipeline with real services"""
    print("🚀 Starting Real GraphRAG Pipeline Test")
    print("="*80)
    
    # Create test document data
    test_document = {
        "document_id": "test_doc_real_002",
        "title": "Test Document: Protein Interactions and Cancer Research - Extended",
        "sections": [
            {
                "_id": "section_real_001",
                "title": "Introduction",
                "text": "The tumor suppressor protein p53 plays a crucial role in maintaining genomic stability and preventing cancer development. It interacts with MDM2 (murine double minute 2), which targets p53 for proteasomal degradation. Mutations in the TP53 gene are associated with various cancers including breast cancer, lung cancer, and colorectal cancer. The p53-MDM2 interaction is a critical regulatory mechanism in cell cycle control."
            },
            {
                "_id": "section_real_002", 
                "title": "Methods",
                "text": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines. The cells were cultured in DMEM (Dulbecco's Modified Eagle Medium) supplemented with 10% fetal bovine serum at 37°C in a 5% CO2 atmosphere. Western blot analysis was performed to detect p53 protein expression levels. Immunoprecipitation assays were used to study the p53-MDM2 protein interaction."
            },
            {
                "_id": "section_real_003",
                "title": "Results",
                "text": "The p53 protein showed significant interaction with MDM2 in our immunoprecipitation assays. TP53 gene mutations were successfully introduced using CRISPR-Cas9 technology. The modified cells exhibited altered p53 expression patterns compared to wild-type controls. These findings confirm the critical role of p53-MDM2 interaction in cancer development."
            }
        ]
    }
    
    print(f"📄 Test Document: {test_document['title']}")
    print(f"📝 Sections: {len(test_document['sections'])}")
    
    try:
        # ============================================================================
        # STEP 1: INITIALIZE REAL GRAPHRAG PIPELINE
        # ============================================================================
        print_step_header(1, "INITIALIZE REAL GRAPHRAG PIPELINE", "Import and initialize the complete GraphRAG pipeline with all services")
        
        print_explanation(
            "What is the GraphRAG Pipeline?",
            "The GraphRAG pipeline is our main processing system that takes documents and extracts knowledge graphs. "
            "It uses LangGraph to orchestrate multiple services: EntityCanonicalizer, ContradictionDetector, "
            "ContradictionResolver, RelationshipConsolidator, and GlobalGraphManager."
        )
        
        # Import the real pipeline
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline, GraphRAGState
        
        print("\n🔧 Initializing Real GraphRAG Pipeline...")
        pipeline = GraphRAGPipeline()
        print("✅ Real GraphRAG pipeline initialized")
        
        # Show pipeline structure
        print_explanation(
            "Pipeline Structure",
            "The pipeline has 8 nodes: map_entities → map_relationships → combine_entities → combine_relationships → "
            "reduce_entities → reduce_relationships → consolidate_relationships → update_global_graph"
        )
        
        # Show services
        print_service_info("EntityCanonicalizer", pipeline.entity_canonicalizer)
        print_service_info("ContradictionDetector", pipeline.contradiction_detector)
        print_service_info("ContradictionResolver", pipeline.contradiction_resolver)
        print_service_info("RelationshipConsolidator", pipeline.relationship_consolidator)
        print_service_info("GlobalGraphManager", pipeline.global_graph_manager)
        
        # ============================================================================
        # STEP 2: TEST INDIVIDUAL PIPELINE NODES
        # ============================================================================
        print_step_header(2, "TEST INDIVIDUAL PIPELINE NODES", "Test each pipeline node step by step with detailed logging")
        
        # Create initial state
        initial_state = GraphRAGState(
            document_id=test_document["document_id"],
            sections=test_document["sections"],
            temp_entities=[],
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
        
        print_data("Initial State", initial_state)
        
        # ============================================================================
        # STEP 3: MAP ENTITIES - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(3, "MAP ENTITIES - REAL PIPELINE NODE", "Use the real _map_entities method from the pipeline")
        
        print_explanation(
            "Map Entities Node",
            "This node processes each section and extracts entities using the LLM. "
            "It calls the OpenAI API with our enhanced entity extraction prompt."
        )
        
        print("\n🤖 Running real _map_entities node...")
        state_after_entities = await pipeline._map_entities(initial_state)
        
        print_data("Entities Extracted", state_after_entities["temp_entities"])
        print(f"\n✅ MAP ENTITIES Complete: {len(state_after_entities['temp_entities'])} entities extracted")
        
        # ============================================================================
        # STEP 4: MAP RELATIONSHIPS - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(4, "MAP RELATIONSHIPS - REAL PIPELINE NODE", "Use the real _map_relationships method from the pipeline")
        
        print_explanation(
            "Map Relationships Node",
            "This node processes each section and extracts relationships between entities using the LLM. "
            "It uses the entities from the previous step and calls the OpenAI API with our enhanced relationship extraction prompt."
        )
        
        print("\n🤖 Running real _map_relationships node...")
        state_after_relationships = await pipeline._map_relationships(state_after_entities)
        
        print_data("Relationships Extracted", state_after_relationships["temp_relationships"])
        print(f"\n✅ MAP RELATIONSHIPS Complete: {len(state_after_relationships['temp_relationships'])} relationships extracted")
        
        # ============================================================================
        # STEP 5: COMBINE ENTITIES - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(5, "COMBINE ENTITIES - REAL PIPELINE NODE", "Use the real _combine_entities method from the pipeline")
        
        print_explanation(
            "Combine Entities Node",
            "This node merges duplicate entities within the document. "
            "For example, if 'p53' appears in multiple sections, it combines them into one entity "
            "with combined aliases, descriptions, and section IDs."
        )
        
        print("\n🔄 Running real _combine_entities node...")
        state_after_combine_entities = await pipeline._combine_entities(state_after_relationships)
        
        print_data("Combined Entities", state_after_combine_entities["doc_entities"])
        print(f"\n✅ COMBINE ENTITIES Complete: {len(state_after_combine_entities['temp_entities'])} temp → {len(state_after_combine_entities['doc_entities'])} doc entities")
        
        # ============================================================================
        # STEP 6: COMBINE RELATIONSHIPS - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(6, "COMBINE RELATIONSHIPS - REAL PIPELINE NODE", "Use the real _combine_relationships method from the pipeline")
        
        print_explanation(
            "Combine Relationships Node",
            "This node merges duplicate relationships within the document using the Noisy-OR formula. "
            "For example, if 'p53 interacts_with MDM2' appears in multiple sections, it combines them "
            "into one relationship with a combined strength."
        )
        
        print("\n🔄 Running real _combine_relationships node...")
        state_after_combine_relationships = await pipeline._combine_relationships(state_after_combine_entities)
        
        print_data("Combined Relationships", state_after_combine_relationships["doc_relationships"])
        print(f"\n✅ COMBINE RELATIONSHIPS Complete: {len(state_after_combine_relationships['temp_relationships'])} temp → {len(state_after_combine_relationships['doc_relationships'])} doc relationships")
        
        # ============================================================================
        # STEP 7: REDUCE ENTITIES - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(7, "REDUCE ENTITIES - REAL PIPELINE NODE", "Use the real _reduce_entities method from the pipeline")
        
        print_explanation(
            "Reduce Entities Node",
            "This node uses the EntityCanonicalizer service to canonicalize entities across documents. "
            "It compares entities from the current document with existing global entities and merges similar ones. "
            "This is where entity canonicalization and stable identifier matching happens."
        )
        
        print("\n🔄 Running real _reduce_entities node...")
        state_after_reduce_entities = await pipeline._reduce_entities(state_after_combine_relationships)
        
        print_data("Final Entities", state_after_reduce_entities["final_entities"])
        print_data("Entity Merges", state_after_reduce_entities["entity_merges"])
        print(f"\n✅ REDUCE ENTITIES Complete: {len(state_after_reduce_entities['doc_entities'])} doc → {len(state_after_reduce_entities['final_entities'])} final entities")
        print(f"   📊 Entity merges: {len(state_after_reduce_entities['entity_merges'])}")
        
        # ============================================================================
        # STEP 8: REDUCE RELATIONSHIPS - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(8, "REDUCE RELATIONSHIPS - REAL PIPELINE NODE", "Use the real _reduce_relationships method from the pipeline")
        
        print_explanation(
            "Reduce Relationships Node",
            "This node uses the ContradictionDetector and ContradictionResolver services to detect and resolve "
            "contradictory relationships. It compares relationships from the current document with existing "
            "global relationships and identifies conflicts."
        )
        
        print("\n🔄 Running real _reduce_relationships node...")
        state_after_reduce_relationships = await pipeline._reduce_relationships(state_after_reduce_entities)
        
        print_data("Final Relationships", state_after_reduce_relationships["final_relationships"])
        print_data("Contradictions", state_after_reduce_relationships["contradictions"])
        print_data("Contradiction Resolutions", state_after_reduce_relationships["contradiction_resolutions"])
        print(f"\n✅ REDUCE RELATIONSHIPS Complete: {len(state_after_reduce_relationships['doc_relationships'])} doc → {len(state_after_reduce_relationships['final_relationships'])} final relationships")
        print(f"   📊 Contradictions: {len(state_after_reduce_relationships['contradictions'])}")
        print(f"   📊 Resolutions: {len(state_after_reduce_relationships['contradiction_resolutions'])}")
        
        # ============================================================================
        # STEP 9: CONSOLIDATE RELATIONSHIPS - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(9, "CONSOLIDATE RELATIONSHIPS - REAL PIPELINE NODE", "Use the real _consolidate_relationships method from the pipeline")
        
        print_explanation(
            "Consolidate Relationships Node",
            "This node uses the RelationshipConsolidator service to consolidate relationships based on multiple criteria. "
            "It groups similar relationships and applies consolidation strategies like consensus, evidence-based, "
            "and temporal consolidation."
        )
        
        print("\n🔄 Running real _consolidate_relationships node...")
        state_after_consolidate = await pipeline._consolidate_relationships(state_after_reduce_relationships)
        
        print_data("Consolidated Relationships", state_after_consolidate["consolidated_relationships"])
        print_data("Consolidation Summary", state_after_consolidate["consolidation_summary"])
        print(f"\n✅ CONSOLIDATE RELATIONSHIPS Complete: {len(state_after_consolidate['final_relationships'])} final → {len(state_after_consolidate['consolidated_relationships'])} consolidated relationships")
        
        # ============================================================================
        # STEP 10: UPDATE GLOBAL GRAPH - REAL PIPELINE NODE
        # ============================================================================
        print_step_header(10, "UPDATE GLOBAL GRAPH - REAL PIPELINE NODE", "Use the real _update_global_graph method from the pipeline")
        
        print_explanation(
            "Update Global Graph Node",
            "This node uses the GlobalGraphManager service to update the global knowledge graph. "
            "It processes the document's entities and relationships against the existing global graph, "
            "applies entity canonicalization, contradiction resolution, and relationship consolidation, "
            "and updates the global graph with the results."
        )
        
        print("\n🔄 Running real _update_global_graph node...")
        final_state = await pipeline._update_global_graph(state_after_consolidate)
        
        print_data("Global Processing Results", final_state["global_processing_results"])
        print(f"\n✅ UPDATE GLOBAL GRAPH Complete: Global graph updated with document processing results")
        
        # ============================================================================
        # FINAL SUMMARY
        # ============================================================================
        print(f"\n{'='*80}")
        print("🎯 REAL GRAPHRAG PIPELINE TEST SUMMARY")
        print(f"{'='*80}")
        
        print(f"📄 Document: {test_document['title']}")
        print(f"📝 Sections processed: {len(test_document['sections'])}")
        print(f"🏷️ Temp entities: {len(final_state['temp_entities'])}")
        print(f"🔗 Temp relationships: {len(final_state['temp_relationships'])}")
        print(f"📋 Doc entities: {len(final_state['doc_entities'])}")
        print(f"📋 Doc relationships: {len(final_state['doc_relationships'])}")
        print(f"✅ Final entities: {len(final_state['final_entities'])}")
        print(f"✅ Final relationships: {len(final_state['final_relationships'])}")
        print(f"🔄 Entity merges: {len(final_state['entity_merges'])}")
        print(f"⚠️ Contradictions: {len(final_state['contradictions'])}")
        print(f"🔄 Contradiction resolutions: {len(final_state['contradiction_resolutions'])}")
        print(f"📊 Consolidated relationships: {len(final_state['consolidated_relationships'])}")
        print(f"🌐 Global processing results: {final_state['global_processing_results']}")
        print(f"❌ Errors: {len(final_state['errors'])}")
        
        if final_state['errors']:
            print(f"\n❌ Errors encountered:")
            for error in final_state['errors']:
                print(f"   - {error}")
        
        print(f"\n🎉 Real GraphRAG pipeline test completed successfully!")
        print(f"📊 All pipeline nodes executed with real services and LLM calls.")
        
        return True
        
    except Exception as e:
        print(f"❌ Real GraphRAG pipeline test failed: {str(e)}")
        logger.exception("Real GraphRAG pipeline test failed")
        return False

async def main():
    """Run the real GraphRAG pipeline test"""
    success = await test_real_graphrag_pipeline()
    
    if success:
        print("\n🎉 Real GraphRAG pipeline test completed successfully!")
        print("📊 Check the logs for detailed information about each pipeline node and service.")
    else:
        print("\n❌ Real GraphRAG pipeline test failed!")
        print("📊 Check the logs for error details.")

if __name__ == "__main__":
    asyncio.run(main())

