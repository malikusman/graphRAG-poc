#!/usr/bin/env python3
"""
Test Real Combine Relationships Node
====================================

This test demonstrates the _combine_relationships node step by step:
1. Shows how duplicate relationships are identified and grouped
2. Demonstrates the Noisy-OR formula for combining relationship strengths
3. Tests the actual _combine_relationships method from the pipeline
4. Explains the RelationshipConsolidator service in detail

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

def create_test_relationships() -> List[Dict[str, Any]]:
    """Create test relationships with duplicates for testing"""
    
    # Create relationships that will have duplicates
    relationships = [
        # p53 -> MDM2 relationships (multiple instances)
        {
            "source_entity": "p53",
            "target_entity": "MDM2", 
            "relationship_type": "interacts_with",
            "relationship_strength": 0.8,
            "description": "p53 protein interacts with MDM2 protein",
            "section_ids": ["section_001"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "p53",
            "target_entity": "MDM2",
            "relationship_type": "interacts_with", 
            "relationship_strength": 0.7,
            "description": "The p53 protein shows strong interaction with MDM2",
            "section_ids": ["section_002"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "p53", 
            "target_entity": "MDM2",
            "relationship_type": "interacts_with",
            "relationship_strength": 0.6,
            "description": "p53 binds to MDM2 in the nucleus",
            "section_ids": ["section_003"],
            "paper_ids": ["test_doc_001"]
        },
        
        # TP53 -> p53 relationships (gene-protein)
        {
            "source_entity": "TP53",
            "target_entity": "p53",
            "relationship_type": "encoded_by",
            "relationship_strength": 0.95,
            "description": "TP53 gene encodes the p53 protein",
            "section_ids": ["section_001"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "TP53", 
            "target_entity": "p53",
            "relationship_type": "encoded_by",
            "relationship_strength": 0.9,
            "description": "The TP53 gene is responsible for encoding p53",
            "section_ids": ["section_002"],
            "paper_ids": ["test_doc_001"]
        },
        
        # MDM2 -> p53 relationships (reverse direction)
        {
            "source_entity": "MDM2",
            "target_entity": "p53", 
            "relationship_type": "regulates",
            "relationship_strength": 0.75,
            "description": "MDM2 regulates p53 stability",
            "section_ids": ["section_001"],
            "paper_ids": ["test_doc_001"]
        },
        {
            "source_entity": "MDM2",
            "target_entity": "p53",
            "relationship_type": "regulates", 
            "relationship_strength": 0.8,
            "description": "MDM2 protein regulates p53 degradation",
            "section_ids": ["section_002"],
            "paper_ids": ["test_doc_001"]
        },
        
        # Unique relationship (no duplicates)
        {
            "source_entity": "CRISPR-Cas9",
            "target_entity": "TP53",
            "relationship_type": "targets",
            "relationship_strength": 0.85,
            "description": "CRISPR-Cas9 can target TP53 gene for editing",
            "section_ids": ["section_003"],
            "paper_ids": ["test_doc_001"]
        }
    ]
    
    return relationships

def print_relationships(relationships: List[Dict[str, Any]], title: str):
    """Print relationships in a nice format"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(relationships)}")
    
    for i, rel in enumerate(relationships, 1):
        # Handle both direct relationship format and consolidated format
        if 'consolidation_result' in rel:
            # This is a consolidated relationship result
            consolidated_rel = rel['consolidation_result']['consolidated_relationship']
            source = consolidated_rel['source_entity']
            target = consolidated_rel['target_entity']
            rel_type = consolidated_rel['relationship_type']
            strength = consolidated_rel['relationship_strength']
            description = consolidated_rel['description']
            sections = consolidated_rel['section_ids']
            evidence_count = consolidated_rel.get('evidence_count', 1)
            strategy = rel['consolidation_result']['consolidation_strategy']
            
            print(f"   {i}. {source} --[{rel_type}]--> {target}")
            print(f"      Strength: {strength:.3f} (Noisy-OR combined)")
            print(f"      Evidence count: {evidence_count}")
            print(f"      Strategy: {strategy}")
            print(f"      Description: {description}")
            print(f"      Sections: {sections}")
        else:
            # This is a direct relationship
            print(f"   {i}. {rel['source_entity']} --[{rel['relationship_type']}]--> {rel['target_entity']}")
            print(f"      Strength: {rel['relationship_strength']:.2f}")
            print(f"      Description: {rel['description']}")
            print(f"      Sections: {rel['section_ids']}")
        print()

def demonstrate_noisy_or_formula():
    """Demonstrate the Noisy-OR formula with examples"""
    print("🧮 NOISY-OR FORMULA DEMONSTRATION")
    print("=" * 80)
    print("📝 The Noisy-OR formula combines multiple relationship strengths:")
    print("   Combined Strength = 1 - (1-p1) × (1-p2) × ... × (1-pn)")
    print("   Where p1, p2, ..., pn are individual relationship strengths")
    print()
    
    # Example 1: p53 -> MDM2 interactions
    print("🔍 Example 1: p53 --[interacts_with]--> MDM2")
    strengths = [0.8, 0.7, 0.6]
    print(f"   Individual strengths: {strengths}")
    
    # Calculate Noisy-OR
    product = 1.0
    for strength in strengths:
        product *= (1 - strength)
    combined_strength = 1 - product
    
    print(f"   Calculation: 1 - (1-{strengths[0]}) × (1-{strengths[1]}) × (1-{strengths[2]})")
    print(f"   Calculation: 1 - {1-strengths[0]:.2f} × {1-strengths[1]:.2f} × {1-strengths[2]:.2f}")
    print(f"   Calculation: 1 - {product:.4f} = {combined_strength:.4f}")
    print(f"   ✅ Combined strength: {combined_strength:.4f}")
    print()
    
    # Example 2: TP53 -> p53 encoded_by
    print("🔍 Example 2: TP53 --[encoded_by]--> p53")
    strengths = [0.95, 0.9]
    print(f"   Individual strengths: {strengths}")
    
    product = 1.0
    for strength in strengths:
        product *= (1 - strength)
    combined_strength = 1 - product
    
    print(f"   Calculation: 1 - (1-{strengths[0]}) × (1-{strengths[1]})")
    print(f"   Calculation: 1 - {1-strengths[0]:.2f} × {1-strengths[1]:.2f}")
    print(f"   Calculation: 1 - {product:.4f} = {combined_strength:.4f}")
    print(f"   ✅ Combined strength: {combined_strength:.4f}")
    print()

def demonstrate_relationship_grouping(relationships: List[Dict[str, Any]]):
    """Demonstrate how relationships are grouped"""
    print("🔍 RELATIONSHIP GROUPING DEMONSTRATION")
    print("=" * 80)
    print("📝 Relationships are grouped by (source, target, relationship_type)")
    print()
    
    # Group relationships
    groups = {}
    for rel in relationships:
        key = (rel['source_entity'], rel['target_entity'], rel['relationship_type'])
        if key not in groups:
            groups[key] = []
        groups[key].append(rel)
    
    print(f"📊 Found {len(groups)} unique relationship groups:")
    print()
    
    for i, (key, group_rels) in enumerate(groups.items(), 1):
        source, target, rel_type = key
        print(f"   {i}. {source} --[{rel_type}]--> {target}")
        print(f"      Count: {len(group_rels)} relationships")
        print(f"      Strengths: {[r['relationship_strength'] for r in group_rels]}")
        print()

async def test_real_combine_relationships():
    """Test the real _combine_relationships method"""
    print("🚀 Starting Real Combine Relationships Test")
    print("=" * 80)
    
    try:
        # Create test data
        print("📄 Test Data Created:")
        relationships = create_test_relationships()
        print(f"   📝 Temp Relationships: {len(relationships)}")
        
        print_relationships(relationships, "Input Temp Relationships")
        
        # Demonstrate the concepts
        demonstrate_noisy_or_formula()
        demonstrate_relationship_grouping(relationships)
        
        print("🔍 STEP 1: CREATE SIMPLE PIPELINE CLASS")
        print("=" * 80)
        print("📝 Create a minimal pipeline class with just the _combine_relationships method")
        
        # Import the state class
        from app.pipelines.graphrag_pipeline import GraphRAGState
        print("✅ GraphRAGState imported successfully")
        
        # Create a simple pipeline class
        class SimpleCombineRelationshipsPipeline:
            def __init__(self):
                from app.services.relationship_consolidator import RelationshipConsolidator
                self.relationship_consolidator = RelationshipConsolidator()
            
            async def _combine_relationships(self, state: GraphRAGState) -> GraphRAGState:
                """Combine relationships using the real service"""
                logger.info(f"Starting relationship combination for document {state['document_id']}")
                
                # Convert dict relationships to Relationship objects
                from app.models.relationships import Relationship
                relationship_objects = []
                for rel_dict in state["temp_relationships"]:
                    rel_obj = Relationship(**rel_dict)
                    relationship_objects.append(rel_obj)
                
                # Use the real RelationshipConsolidator service
                consolidation_result = await self.relationship_consolidator.consolidate_relationships(
                    relationships=relationship_objects
                )
                
                # Extract consolidated relationships from result
                consolidated_relationships = consolidation_result.get("consolidated_relationships", [])
                
                logger.info(f"Relationship combination complete: {len(consolidated_relationships)} consolidated relationships")
                
                # Update state
                state["consolidated_relationships"] = consolidated_relationships
                return state
        
        print("✅ SimpleCombineRelationshipsPipeline class created successfully")
        
        print("\n🔍 STEP 2: TEST THE REAL METHOD")
        print("=" * 80)
        print("📝 Call the actual _combine_relationships method with our test data")
        
        # Create test state
        test_state = GraphRAGState(
            document_id="test_doc_001",
            temp_relationships=relationships,
            consolidated_relationships=[],
            temp_entities=[],  # Required field
            unique_entities=[],  # Required field
            temp_sections=[],  # Required field
            sections=[],  # Required field
            relationships=[],  # Required field
            contradictions=[],  # Required field
            resolution_summary={},  # Required field
            global_processing_results={}  # Required field
        )
        print("✅ Test state created successfully")
        
        # Create pipeline instance
        pipeline = SimpleCombineRelationshipsPipeline()
        print("✅ Pipeline instance created successfully")
        
        print("\n🤖 Calling real _combine_relationships method...")
        result_state = await pipeline._combine_relationships(test_state)
        
        print("\n📊 Real Pipeline Result:")
        print(f"🔍 Debug: Consolidated relationships structure:")
        for i, rel in enumerate(result_state["consolidated_relationships"][:2]):  # Show first 2
            print(f"   {i+1}. {type(rel)}: {rel}")
        print()
        print_relationships(result_state["consolidated_relationships"], "Consolidated Relationships")
        print("✅ Real method call successful!")
        
        print("\n🔍 STEP 3: ANALYZE THE RESULTS")
        print("=" * 80)
        print("📝 Compare input vs output and analyze the consolidation")
        
        input_count = len(relationships)
        output_count = len(result_state["consolidated_relationships"])
        consolidated_count = input_count - output_count
        
        print(f"📊 Results Analysis:")
        print(f"   Input relationships: {input_count}")
        print(f"   Output relationships: {output_count}")
        print(f"   Relationships consolidated: {consolidated_count}")
        print()
        
        print("🔄 Relationship Consolidation Details:")
        for i, rel in enumerate(result_state["consolidated_relationships"], 1):
            if 'consolidation_result' in rel:
                consolidated_rel = rel['consolidation_result']['consolidated_relationship']
                strategy = rel['consolidation_result']['consolidation_strategy']
                print(f"   {i}. {consolidated_rel['source_entity']} --[{consolidated_rel['relationship_type']}]--> {consolidated_rel['target_entity']}")
                print(f"      Combined strength: {consolidated_rel['relationship_strength']:.4f}")
                print(f"      Evidence count: {consolidated_rel.get('evidence_count', 1)}")
                print(f"      Strategy: {strategy}")
                print(f"      Description: {consolidated_rel['description']}")
            else:
                print(f"   {i}. {rel['source_entity']} --[{rel['relationship_type']}]--> {rel['target_entity']}")
                print(f"      Strength: {rel['relationship_strength']:.4f}")
                print(f"      Description: {rel['description']}")
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
        
        print("\n🤖 Calling full pipeline _combine_relationships method...")
        full_result_state = await full_pipeline._combine_relationships(test_state)
        
        print("\n📊 Full Pipeline Result:")
        print_relationships(full_result_state["consolidated_relationships"], "Full Pipeline Consolidated Relationships")
        print("✅ Full pipeline method call successful!")
        
        # Compare results
        if len(result_state["consolidated_relationships"]) == len(full_result_state["consolidated_relationships"]):
            print("🎉 Results match! Both methods produced the same number of relationships.")
        else:
            print("⚠️ Results differ between simple and full pipeline methods.")
        
        print("\n🎉 Real combine relationships test completed successfully!")
        print("📊 We successfully called the real _combine_relationships method!")
        
    except Exception as e:
        logger.error(f"Real combine relationships test failed: {str(e)}")
        print(f"❌ Real combine relationships test failed!")
        print(f"📊 Check the logs for error details.")
        raise

if __name__ == "__main__":
    asyncio.run(test_real_combine_relationships())
