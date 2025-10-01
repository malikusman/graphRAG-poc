#!/usr/bin/env python3
"""
Test Real Reduce Relationships Node
===================================

This test demonstrates the _reduce_relationships node step by step:
1. Shows how contradictions are detected between relationships
2. Demonstrates different contradiction resolution strategies
3. Tests the actual _reduce_relationships method from the pipeline
4. Explains the ContradictionDetector and ContradictionResolver services in detail

Author: AI Assistant
Date: 2025-09-29
"""

import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_relationships_with_contradictions() -> List[Dict[str, Any]]:
    """Create test relationships with contradictions for testing"""
    
    # Create relationships that will have contradictions
    relationships = [
        # Contradiction 1: p53 and apoptosis - conflicting information
        {
            "source_entity": "p53",
            "target_entity": "apoptosis",
            "relationship_type": "promotes",
            "relationship_strength": 0.85,
            "description": "p53 promotes apoptosis in response to DNA damage",
            "section_ids": ["section_001"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "p53",
            "target_entity": "apoptosis", 
            "relationship_type": "inhibits",
            "relationship_strength": 0.75,
            "description": "p53 inhibits apoptosis under normal conditions",
            "section_ids": ["section_002"],
            "paper_ids": ["test_doc_001"]
        },
        
        # Contradiction 2: MDM2 and p53 - conflicting regulation
        {
            "source_entity": "MDM2",
            "target_entity": "p53",
            "relationship_type": "activates",
            "relationship_strength": 0.8,
            "description": "MDM2 activates p53 in response to stress",
            "section_ids": ["section_003"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "MDM2",
            "target_entity": "p53",
            "relationship_type": "inhibits", 
            "relationship_strength": 0.9,
            "description": "MDM2 inhibits p53 by targeting it for degradation",
            "section_ids": ["section_004"],
            "paper_ids": ["test_doc_001"]
        },
        
        # Contradiction 3: TP53 and cancer - conflicting effects
        {
            "source_entity": "TP53",
            "target_entity": "cancer",
            "relationship_type": "prevents",
            "relationship_strength": 0.95,
            "description": "TP53 prevents cancer by regulating cell cycle",
            "section_ids": ["section_005"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "TP53",
            "target_entity": "cancer",
            "relationship_type": "causes",
            "relationship_strength": 0.7,
            "description": "Mutant TP53 causes cancer development",
            "section_ids": ["section_006"],
            "paper_ids": ["test_doc_001"]
        },
        
        # No contradiction - clear relationship
        {
            "source_entity": "CRISPR-Cas9",
            "target_entity": "DNA",
            "relationship_type": "targets",
            "relationship_strength": 0.9,
            "description": "CRISPR-Cas9 targets specific DNA sequences for editing",
            "section_ids": ["section_007"],
            "paper_ids": ["test_doc_001"]
        },
        
        # Temporal contradiction - different time periods
        {
            "source_entity": "p53",
            "target_entity": "cell_cycle",
            "relationship_type": "regulates",
            "relationship_strength": 0.8,
            "description": "p53 regulates cell cycle progression (1990s studies)",
            "section_ids": ["section_008"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "p53",
            "target_entity": "cell_cycle",
            "relationship_type": "regulates",
            "relationship_strength": 0.85,
            "description": "p53 blocks cell cycle at G1 checkpoint (recent studies)",
            "section_ids": ["section_009"],
            "paper_ids": ["test_doc_001"]
        }
    ]
    
    return relationships

def print_relationships(relationships: List[Dict[str, Any]], title: str):
    """Print relationships in a nice format"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(relationships)}")
    
    for i, rel in enumerate(relationships, 1):
        print(f"   {i}. {rel['source_entity']} --[{rel['relationship_type']}]--> {rel['target_entity']}")
        print(f"      Strength: {rel['relationship_strength']:.2f}")
        print(f"      Description: {rel['description']}")
        print(f"      Sections: {rel['section_ids']}")
        print()

def demonstrate_contradiction_detection():
    """Demonstrate how contradictions are detected"""
    print("🔍 CONTRADICTION DETECTION DEMONSTRATION")
    print("=" * 80)
    print("📝 Contradictions are detected by analyzing relationship pairs that:")
    print("   1. Involve the same entities (source and target)")
    print("   2. Have conflicting relationship types")
    print("   3. Express opposite or contradictory meanings")
    print()
    
    print("🎯 Types of Contradictions:")
    print("   📌 Direct Contradiction: promotes vs inhibits")
    print("   📌 Opposite Effects: activates vs inhibits") 
    print("   📌 Contextual Contradiction: prevents vs causes (different contexts)")
    print("   📌 Temporal Contradiction: different time periods, different findings")
    print()
    
    print("🧠 How LLM Detects Contradictions:")
    print("   1. Analyzes relationship semantics and context")
    print("   2. Considers biological/biomedical knowledge")
    print("   3. Evaluates strength and confidence of evidence")
    print("   4. Determines if relationships are truly contradictory")
    print()

def demonstrate_contradiction_resolution():
    """Demonstrate different contradiction resolution strategies"""
    print("🛠️ CONTRADICTION RESOLUTION STRATEGIES")
    print("=" * 80)
    print("📝 When contradictions are found, the system uses different strategies:")
    print()
    
    print("🎯 Strategy 1: Evidence-Based Resolution")
    print("   When: One relationship has stronger evidence")
    print("   Example: Strength 0.95 vs 0.7 → Choose 0.95")
    print("   Action: Select relationship with higher confidence")
    print()
    
    print("🎯 Strategy 2: Consensus-Based Resolution")
    print("   When: Multiple sources support one interpretation")
    print("   Example: 3 papers say 'promotes', 1 says 'inhibits' → Choose 'promotes'")
    print("   Action: Select most commonly supported relationship")
    print()
    
    print("🎯 Strategy 3: Temporal Resolution")
    print("   When: Contradictions are time-dependent")
    print("   Example: Old studies vs recent studies → Prefer recent")
    print("   Action: Select most recent or most current evidence")
    print()
    
    print("🎯 Strategy 4: Context-Dependent Resolution")
    print("   When: Contradictions depend on context")
    print("   Example: 'TP53 prevents cancer' vs 'mutant TP53 causes cancer'")
    print("   Action: Clarify context or create separate relationships")
    print()
    
    print("🎯 Strategy 5: Manual Review Flagging")
    print("   When: Cannot resolve automatically")
    print("   Example: Complex contradictions requiring expert knowledge")
    print("   Action: Flag for human expert review")
    print()

def demonstrate_contradiction_examples():
    """Show specific examples of contradictions from our test data"""
    print("📋 CONTRADICTION EXAMPLES FROM TEST DATA")
    print("=" * 80)
    
    print("🔍 Example 1: p53 and Apoptosis")
    print("   Relationship A: p53 --[promotes]--> apoptosis (strength: 0.85)")
    print("   Relationship B: p53 --[inhibits]--> apoptosis (strength: 0.75)")
    print("   Contradiction: promotes vs inhibits")
    print("   Resolution Strategy: Evidence-based (choose 0.85)")
    print("   Result: p53 promotes apoptosis (with context clarification)")
    print()
    
    print("🔍 Example 2: MDM2 and p53")
    print("   Relationship A: MDM2 --[activates]--> p53 (strength: 0.8)")
    print("   Relationship B: MDM2 --[inhibits]--> p53 (strength: 0.9)")
    print("   Contradiction: activates vs inhibits")
    print("   Resolution Strategy: Evidence-based (choose 0.9)")
    print("   Result: MDM2 inhibits p53 (with context clarification)")
    print()
    
    print("🔍 Example 3: TP53 and Cancer")
    print("   Relationship A: TP53 --[prevents]--> cancer (strength: 0.95)")
    print("   Relationship B: TP53 --[causes]--> cancer (strength: 0.7)")
    print("   Contradiction: prevents vs causes")
    print("   Resolution Strategy: Context-dependent")
    print("   Result: 'Normal TP53 prevents cancer, mutant TP53 causes cancer'")
    print()

async def test_real_reduce_relationships():
    """Test the real _reduce_relationships method"""
    print("🚀 Starting Real Reduce Relationships Test")
    print("=" * 80)
    
    try:
        # Create test data
        print("📄 Test Data Created:")
        relationships = create_test_relationships_with_contradictions()
        print(f"   📝 Input Relationships: {len(relationships)}")
        
        print_relationships(relationships, "Input Relationships with Contradictions")
        
        # Demonstrate the concepts
        demonstrate_contradiction_detection()
        demonstrate_contradiction_resolution()
        demonstrate_contradiction_examples()
        
        print("🔍 STEP 1: CREATE SIMPLE PIPELINE CLASS")
        print("=" * 80)
        print("📝 Create a minimal pipeline class with just the _reduce_relationships method")
        
        # Import the state class
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        # Create a simple pipeline class
        class SimpleReduceRelationshipsPipeline:
            def __init__(self):
                from app.services.contradiction_detector import ContradictionDetector
                from app.services.contradiction_resolver import ContradictionResolver
                self.contradiction_detector = ContradictionDetector()
                self.contradiction_resolver = ContradictionResolver()
            
            async def _reduce_relationships(self, state: GraphRAGState) -> GraphRAGState:
                """Reduce relationships using the real services"""
                logger.info(f"Starting relationship reduction for document {state['document_id']}")
                
                # Convert dict relationships to Relationship objects
                from app.models.relationships import Relationship
                relationship_objects = []
                for rel_dict in state["doc_relationships"]:
                    rel_obj = Relationship(**rel_dict)
                    relationship_objects.append(rel_obj)
                
                # Create context information
                context_info = {
                    "document_id": state["document_id"],
                    "total_relationships": len(relationship_objects),
                    "publication_year": None,
                    "paper_source": "test_document",
                    "section_types": ["introduction", "methods", "results", "discussion"]
                }
                
                # Process contradiction detection with resolver
                contradiction_results = await self.contradiction_detector.process_contradiction_detection_with_resolver(
                    relationship_objects, 
                    context_info, 
                    self.contradiction_resolver
                )
                
                logger.info(f"Relationship reduction complete: {len(contradiction_results.get('contradictions', []))} contradictions found")
                
                # Update state
                state["contradictions"] = contradiction_results.get("contradictions", [])
                state["contradiction_resolutions"] = contradiction_results.get("resolutions", [])
                state["resolution_summary"] = contradiction_results.get("resolution_summary", {})
                
                return state
        
        print("✅ SimpleReduceRelationshipsPipeline class created successfully")
        
        print("\n🔍 STEP 2: TEST THE REAL METHOD")
        print("=" * 80)
        print("📝 Call the actual _reduce_relationships method with our test data")
        
        # Create test state
        test_state = GraphRAGState(
            document_id="test_doc_001",
            temp_relationships=relationships,
            consolidated_relationships=[],
            temp_entities=[],
            unique_entities=[],
            temp_sections=[],
            sections=[],
            relationships=[],
            doc_relationships=relationships,  # This is what _reduce_relationships uses
            contradictions=[],
            resolution_summary={},
            global_processing_results={}
        )
        print("✅ Test state created successfully")
        
        # Create pipeline instance
        pipeline = SimpleReduceRelationshipsPipeline()
        print("✅ Pipeline instance created successfully")
        
        print("\n🤖 Calling real _reduce_relationships method...")
        result_state = await pipeline._reduce_relationships(test_state)
        
        print("\n📊 Real Pipeline Result:")
        print(f"🔍 Contradictions Found: {len(result_state['contradictions'])}")
        print(f"🔍 Resolutions Applied: {len(result_state['contradiction_resolutions'])}")
        
        # Print contradictions found
        if result_state['contradictions']:
            print("\n🚨 Contradictions Detected:")
            for i, contradiction in enumerate(result_state['contradictions'], 1):
                print(f"   {i}. {contradiction.get('contradiction_type', 'unknown')}")
                print(f"      Severity: {contradiction.get('severity', 'unknown')}")
                print(f"      Entities: {contradiction.get('entities', [])}")
                print(f"      Description: {contradiction.get('description', 'No description')}")
                print()
        
        # Print resolutions applied
        if result_state['contradiction_resolutions']:
            print("\n🛠️ Resolutions Applied:")
            for i, resolution in enumerate(result_state['contradiction_resolutions'], 1):
                print(f"   {i}. Strategy: {resolution.get('resolution', 'unknown')}")
                print(f"      Confidence: {resolution.get('confidence', 0.0):.2f}")
                print(f"      Description: {resolution.get('resolution_description', 'No description')}")
                print()
        
        print("✅ Real method call successful!")
        
        print("\n🔍 STEP 3: ANALYZE THE RESULTS")
        print("=" * 80)
        print("📝 Analyze contradiction detection and resolution")
        
        contradictions_found = len(result_state["contradictions"])
        resolutions_applied = len(result_state["contradiction_resolutions"])
        
        print(f"📊 Results Analysis:")
        print(f"   Input relationships: {len(relationships)}")
        print(f"   Contradictions found: {contradictions_found}")
        print(f"   Resolutions applied: {resolutions_applied}")
        print(f"   Resolution rate: {(resolutions_applied/contradictions_found*100) if contradictions_found > 0 else 0:.1f}%")
        print()
        
        print("🔍 STEP 4: TRY THE FULL PIPELINE CLASS")
        print("=" * 80)
        print("📝 Try to use the actual GraphRAGPipeline class")
        
        # Import full pipeline
        from app.pipelines.graphrag_pipeline import GraphRAGPipeline
        print("✅ Full GraphRAGPipeline imported successfully")
        
        # Create full pipeline instance
        full_pipeline = GraphRAGPipeline()
        print("✅ Full pipeline instance created successfully")
        
        print("\n🤖 Calling full pipeline _reduce_relationships method...")
        full_result_state = await full_pipeline._reduce_relationships(test_state)
        
        print("\n📊 Full Pipeline Result:")
        print(f"🔍 Contradictions Found: {len(full_result_state['contradictions'])}")
        print(f"🔍 Resolutions Applied: {len(full_result_state['contradiction_resolutions'])}")
        print("✅ Full pipeline method call successful!")
        
        # Compare results
        if len(result_state["contradictions"]) == len(full_result_state["contradictions"]):
            print("🎉 Results match! Both methods found the same number of contradictions.")
        else:
            print("⚠️ Results differ between simple and full pipeline methods.")
        
        print("\n🎉 Real reduce relationships test completed successfully!")
        print("📊 We successfully called the real _reduce_relationships method!")
        
    except Exception as e:
        logger.error(f"Real reduce relationships test failed: {str(e)}")
        print(f"❌ Real reduce relationships test failed!")
        print(f"📊 Check the logs for error details.")
        raise

if __name__ == "__main__":
    asyncio.run(test_real_reduce_relationships())

