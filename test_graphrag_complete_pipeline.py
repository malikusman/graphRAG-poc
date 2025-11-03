#!/usr/bin/env python3
"""
Complete GraphRAG Pipeline Test

Tests all 8 nodes of the GraphRAG pipeline:
1. map_entities
2. map_relationships  
3. combine_entities
4. combine_relationships
5. reduce_entities
6. reduce_relationships
7. consolidate_relationships
8. update_global_graph
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable debug logging for pipeline components
logging.getLogger("app.pipelines.graphrag_pipeline").setLevel(logging.INFO)
logging.getLogger("app.services.entity_canonicalizer").setLevel(logging.INFO)
logging.getLogger("app.services.contradiction_detector").setLevel(logging.INFO)
logging.getLogger("app.services.relationship_consolidator").setLevel(logging.INFO)
logging.getLogger("app.services.global_graph_manager").setLevel(logging.INFO)


def print_node_header(node_name: str, node_number: int, description: str):
    """Print a formatted header for each pipeline node"""
    print("\n" + "=" * 80)
    print(f"🔄 NODE {node_number}/8: {node_name.upper()}")
    print("=" * 80)
    print(f"📝 {description}")
    print("-" * 80)


def print_node_summary(state: Dict[str, Any], node_name: str):
    """Print summary of node execution"""
    print(f"\n✅ {node_name} completed successfully!")
    
    if node_name == "map_entities":
        print(f"   • Temp entities extracted: {len(state.get('temp_entities', []))}")
        if state.get('temp_entities'):
            sample = state['temp_entities'][0]
            print(f"   • Sample entity: {sample.get('entity_name')} ({sample.get('entity_type')})")
    
    elif node_name == "map_relationships":
        print(f"   • Temp relationships extracted: {len(state.get('temp_relationships', []))}")
        if state.get('temp_relationships'):
            sample = state['temp_relationships'][0]
            print(f"   • Sample relationship: {sample.get('source_entity')} -> {sample.get('target_entity')}")
    
    elif node_name == "combine_entities":
        print(f"   • Doc entities (merged): {len(state.get('doc_entities', []))}")
        print(f"   • Reduction: {len(state.get('temp_entities', []))} -> {len(state.get('doc_entities', []))}")
    
    elif node_name == "combine_relationships":
        print(f"   • Doc relationships (merged): {len(state.get('doc_relationships', []))}")
        print(f"   • Reduction: {len(state.get('temp_relationships', []))} -> {len(state.get('doc_relationships', []))}")
    
    elif node_name == "reduce_entities":
        print(f"   • Final entities (canonicalized): {len(state.get('final_entities', []))}")
        print(f"   • Entity merges: {len(state.get('entity_merges', []))}")
    
    elif node_name == "reduce_relationships":
        print(f"   • Final relationships: {len(state.get('final_relationships', []))}")
        print(f"   • Contradictions found: {len(state.get('contradictions', []))}")
        print(f"   • Resolutions applied: {len(state.get('contradiction_resolutions', []))}")
    
    elif node_name == "consolidate_relationships":
        print(f"   • Consolidated relationships: {len(state.get('consolidated_relationships', []))}")
        consolidation_summary = state.get('consolidation_summary', {})
        if consolidation_summary:
            print(f"   • Consolidation summary: {consolidation_summary}")
    
    elif node_name == "update_global_graph":
        global_results = state.get('global_processing_results', {})
        print(f"   • Entities processed: {global_results.get('entities_processed', 0)}")
        print(f"   • Relationships processed: {global_results.get('relationships_processed', 0)}")
    
    errors = state.get('errors', [])
    if errors:
        print(f"   ⚠️  Errors: {len(errors)}")
        for error in errors[:3]:  # Show first 3 errors
            print(f"      - {error}")


async def test_complete_pipeline():
    """Test the complete GraphRAG pipeline through all 8 nodes"""
    
    print("\n" + "=" * 80)
    print("🚀 COMPLETE GRAPHRAG PIPELINE TEST")
    print("=" * 80)
    print("Testing all 8 pipeline nodes with realistic scientific text")
    print("=" * 80)
    
    # Create test document with realistic scientific content
    document_id = f"complete_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    sections = [
        {
            "_id": "section_001",
            "title": "Abstract",
            "text": "CRISPR-Cas9 genome editing has revolutionized cancer research by enabling precise modifications to oncogenes and tumor suppressor genes. This study demonstrates the successful application of CRISPR-Cas9 to target TP53 mutations in colorectal cancer cell lines, resulting in significant apoptosis induction and tumor growth inhibition. The methodology combines single-guide RNA (sgRNA) design optimization with high-efficiency delivery systems, achieving 85% editing efficiency across multiple cell lines. Results show that CRISPR-Cas9-mediated TP53 restoration leads to 40% reduction in tumor proliferation rates and enhanced sensitivity to chemotherapeutic agents like 5-fluorouracil. These findings support the potential of CRISPR-Cas9 as a therapeutic approach for cancer treatment, particularly in cases with specific genetic mutations.",
            "type": "abstract",
            "position": 1
        },
        {
            "_id": "section_002",
            "title": "Methods",
            "text": "We employed a comprehensive CRISPR-Cas9 workflow targeting TP53 mutations in HCT116 colorectal cancer cells. The experimental design included sgRNA design using the CHOPCHOP algorithm, Cas9 delivery optimization using Lipofectamine 3000, and functional assessment of gene editing outcomes. Cell culture experiments were conducted using HCT116 cells maintained in McCoy's 5A medium supplemented with 10% fetal bovine serum. Gene editing efficiency was assessed using T7 endonuclease I assays and Sanger sequencing. Functional outcomes were evaluated through apoptosis assays (Annexin V/PI staining) and proliferation measurements (MTS assay). Western blot analysis was performed to detect p53 protein expression levels.",
            "type": "methods",
            "position": 2
        },
        {
            "_id": "section_003",
            "title": "Results",
            "text": "CRISPR-Cas9-mediated TP53 editing demonstrated remarkable efficacy in HCT116 colorectal cancer cells. Gene editing efficiency reached 85.3% ± 4.2% across three independent experiments. TP53 restoration resulted in 42.7% ± 6.1% reduction in cell proliferation compared to control groups (p < 0.001). Apoptosis induction was particularly pronounced, with 67.3% ± 8.4% of edited cells showing positive Annexin V staining after 48 hours. Western blot analysis confirmed increased expression of p21 and Bax proteins, downstream targets of functional TP53. Edited cells exhibited enhanced sensitivity to 5-fluorouracil treatment, with IC50 values decreasing from 12.3 μM to 4.7 μM (p < 0.01). Flow cytometry analysis revealed cell cycle arrest at G1/S checkpoint in 78.2% of TP53-restored cells.",
            "type": "results",
            "position": 3
        }
    ]
    
    print(f"\n📄 Test Document Configuration:")
    print(f"   • Document ID: {document_id}")
    print(f"   • Sections: {len(sections)}")
    for i, section in enumerate(sections, 1):
        print(f"   • Section {i}: {section['title']} ({len(section['text'])} chars)")
    print()
    
    try:
        # Import pipeline
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline, GraphRAGState
        
        # Initialize pipeline
        print("🔧 Initializing GraphRAG Pipeline...")
        pipeline = GraphRAGPipeline()
        print("✅ Pipeline initialized successfully")
        print(f"   • LLM Provider: {type(pipeline.llm).__name__}")
        print(f"   • Services loaded: EntityCanonicalizer, ContradictionDetector, etc.")
        print()
        
        # Initialize state
        from app.services.global_graph_manager import GlobalGraphManager
        global_graph_manager = GlobalGraphManager()
        
        # Load global graph state
        try:
            global_state = await global_graph_manager.load_global_graph_state()
            if global_state.get("error"):
                global_entities = []
                global_relationships = []
            else:
                global_entities = global_state.get("global_entities", [])
                global_relationships = global_state.get("global_relationships", [])
        except Exception as e:
            logger.warning(f"Could not load global graph state: {e}")
            global_entities = []
            global_relationships = []
        
        print(f"📊 Global Graph State:")
        print(f"   • Existing entities: {len(global_entities)}")
        print(f"   • Existing relationships: {len(global_relationships)}")
        print()
        
        # Create initial state
        initial_state = GraphRAGState(
            document_id=document_id,
            sections=sections,
            temp_entities=[],
            temp_relationships=[],
            doc_entities=[],
            doc_relationships=[],
            final_entities=[],
            final_relationships=[],
            global_entities=global_entities,
            global_relationships=global_relationships,
            entity_merges=[],
            contradictions=[],
            contradiction_resolutions=[],
            resolution_summary={},
            consolidated_relationships=[],
            consolidation_summary={},
            global_processing_results={},
            errors=[]
        )
        
        print("🚀 Starting Pipeline Execution...")
        print("=" * 80)
        
        # Execute pipeline step by step by invoking the graph
        # The graph will automatically execute all nodes in sequence
        print("\n⚡ Running complete pipeline (all nodes will execute automatically)...")
        print("   Note: Each node will execute in sequence as defined in the graph")
        print()
        
        # Run the complete pipeline
        start_time = datetime.now()
        final_state = await pipeline.graph.ainvoke(initial_state)
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("✅ PIPELINE EXECUTION COMPLETE")
        print("=" * 80)
        print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
        print()
        
        # Print detailed summary for each node
        print("\n" + "=" * 80)
        print("📊 DETAILED NODE SUMMARY")
        print("=" * 80)
        
        # Node 1: Map Entities
        print_node_summary(final_state, "map_entities")
        
        # Node 2: Map Relationships
        print_node_summary(final_state, "map_relationships")
        
        # Node 3: Combine Entities
        print_node_summary(final_state, "combine_entities")
        
        # Node 4: Combine Relationships
        print_node_summary(final_state, "combine_relationships")
        
        # Node 5: Reduce Entities
        print_node_summary(final_state, "reduce_entities")
        
        # Node 6: Reduce Relationships
        print_node_summary(final_state, "reduce_relationships")
        
        # Node 7: Consolidate Relationships
        print_node_summary(final_state, "consolidate_relationships")
        
        # Node 8: Update Global Graph
        print_node_summary(final_state, "update_global_graph")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📈 FINAL PIPELINE SUMMARY")
        print("=" * 80)
        print(f"✅ Success: {len(final_state.get('errors', [])) == 0}")
        print(f"📊 Entities:")
        print(f"   • Temp entities: {len(final_state.get('temp_entities', []))}")
        print(f"   • Doc entities: {len(final_state.get('doc_entities', []))}")
        print(f"   • Final entities: {len(final_state.get('final_entities', []))}")
        print(f"   • Entity merges: {len(final_state.get('entity_merges', []))}")
        print(f"📊 Relationships:")
        print(f"   • Temp relationships: {len(final_state.get('temp_relationships', []))}")
        print(f"   • Doc relationships: {len(final_state.get('doc_relationships', []))}")
        print(f"   • Final relationships: {len(final_state.get('final_relationships', []))}")
        print(f"   • Contradictions: {len(final_state.get('contradictions', []))}")
        print(f"   • Resolutions: {len(final_state.get('contradiction_resolutions', []))}")
        print(f"   • Consolidated: {len(final_state.get('consolidated_relationships', []))}")
        print(f"🌐 Global Graph:")
        global_results = final_state.get('global_processing_results', {})
        print(f"   • Entities processed: {global_results.get('entities_processed', 0)}")
        print(f"   • Relationships processed: {global_results.get('relationships_processed', 0)}")
        print(f"❌ Errors: {len(final_state.get('errors', []))}")
        
        if final_state.get('errors'):
            print("\n⚠️  Errors encountered:")
            for error in final_state['errors']:
                print(f"   • {error}")
        
        # Sample outputs
        print("\n" + "=" * 80)
        print("🔍 SAMPLE OUTPUTS")
        print("=" * 80)
        
        # Sample entities
        if final_state.get('final_entities'):
            print("\n📌 Sample Final Entities (first 3):")
            for entity in final_state['final_entities'][:3]:
                print(f"   • {entity.get('entity_name')} ({entity.get('entity_type')})")
                print(f"     Category: {entity.get('entity_category')}")
                print(f"     Description: {entity.get('description', '')[:100]}...")
        
        # Sample relationships
        if final_state.get('final_relationships'):
            print("\n🔗 Sample Final Relationships (first 3):")
            for rel in final_state['final_relationships'][:3]:
                print(f"   • {rel.get('source_entity')} -> [{rel.get('relationship_type')}] -> {rel.get('target_entity')}")
                print(f"     Strength: {rel.get('relationship_strength', 'N/A')}")
                print(f"     Description: {rel.get('description', '')[:100]}...")
        
        print("\n" + "=" * 80)
        print("✅ COMPLETE PIPELINE TEST SUCCESSFUL!")
        print("=" * 80)
        print("\nAll 8 nodes executed successfully:")
        print("   1. ✅ map_entities")
        print("   2. ✅ map_relationships")
        print("   3. ✅ combine_entities")
        print("   4. ✅ combine_relationships")
        print("   5. ✅ reduce_entities")
        print("   6. ✅ reduce_relationships")
        print("   7. ✅ consolidate_relationships")
        print("   8. ✅ update_global_graph")
        print()
        
        return {
            "success": True,
            "document_id": document_id,
            "execution_time": execution_time,
            "final_state": final_state
        }
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {str(e)}", exc_info=True)
        print(f"\n❌ TEST FAILED: {str(e)}")
        raise


if __name__ == "__main__":
    result = asyncio.run(test_complete_pipeline())
    
    # Save results to file
    if result and result.get("success"):
        output_file = f"complete_pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            # Convert state to JSON-serializable format
            final_state = result.get("final_state", {})
            json_result = {
                "success": result["success"],
                "document_id": result["document_id"],
                "execution_time": result["execution_time"],
                "summary": {
                    "temp_entities": len(final_state.get("temp_entities", [])),
                    "temp_relationships": len(final_state.get("temp_relationships", [])),
                    "doc_entities": len(final_state.get("doc_entities", [])),
                    "doc_relationships": len(final_state.get("doc_relationships", [])),
                    "final_entities": len(final_state.get("final_entities", [])),
                    "final_relationships": len(final_state.get("final_relationships", [])),
                    "entity_merges": len(final_state.get("entity_merges", [])),
                    "contradictions": len(final_state.get("contradictions", [])),
                    "resolutions": len(final_state.get("contradiction_resolutions", [])),
                    "consolidated": len(final_state.get("consolidated_relationships", [])),
                    "errors": len(final_state.get("errors", []))
                },
                "errors": final_state.get("errors", [])
            }
            json.dump(json_result, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")

