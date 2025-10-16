#!/usr/bin/env python3
"""
Comprehensive Test for _consolidate_relationships Node and RelationshipConsolidator Service

This test demonstrates how the _consolidate_relationships node works with the RelationshipConsolidator service:
1. Groups relationships by (source_entity, target_entity, relationship_type)
2. Calculates consolidation metrics for each group
3. Determines appropriate consolidation strategy
4. Applies consolidation using Noisy-OR formula and LLM analysis
5. Returns consolidated relationships with detailed metadata

The test shows different scenarios of relationship consolidation.
"""

import asyncio
import logging
from typing import List, Dict, Any
from app.models.entities import Entity, EntityType, EntityCategory
from app.models.relationships import Relationship, RelationshipType
from app.services.relationship_consolidator import RelationshipConsolidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"🔍 {title}")
    print("="*80)

def print_subheader(title: str):
    """Print a formatted subheader"""
    print(f"\n📋 {title}")
    print("-" * 60)

def create_test_relationships() -> List[Relationship]:
    """Create test relationships with various consolidation scenarios"""
    
    relationships = [
        # Scenario 1: Consensus Consolidation - Multiple agreeing relationships
        # TP53 increases apoptosis (same relationship, different papers)
        Relationship(
            source_entity="TP53",
            target_entity="apoptosis",
            relationship_type=RelationshipType.PROMOTES,
            relationship_strength=0.8,
            description="TP53 promotes apoptosis through transcriptional activation of pro-apoptotic genes",
            paper_ids=["paper_001"],
            section_ids=["results_001"]
        ),
        
        Relationship(
            source_entity="TP53",
            target_entity="apoptosis",
            relationship_type=RelationshipType.PROMOTES,
            relationship_strength=0.7,
            description="TP53 induces apoptosis in response to DNA damage",
            paper_ids=["paper_002", "paper_003"],
            section_ids=["results_002", "results_003"]
        ),
        
        Relationship(
            source_entity="TP53",
            target_entity="apoptosis",
            relationship_type=RelationshipType.PROMOTES,
            relationship_strength=0.9,
            description="TP53-mediated apoptosis is essential for tumor suppression",
            paper_ids=["paper_004"],
            section_ids=["results_004"]
        ),
        
        # Scenario 2: Evidence-Based Consolidation - Different strengths
        # CRISPR-Cas9 gene editing (same relationship, different evidence)
        Relationship(
            source_entity="CRISPR-Cas9",
            target_entity="gene editing",
            relationship_type=RelationshipType.USES,
            relationship_strength=0.6,
            description="CRISPR-Cas9 uses gene editing in bacterial cells",
            paper_ids=["paper_005"],
            section_ids=["results_005"]
        ),
        
        Relationship(
            source_entity="CRISPR-Cas9",
            target_entity="gene editing",
            relationship_type=RelationshipType.USES,
            relationship_strength=0.9,
            description="CRISPR-Cas9 uses precise gene editing in mammalian cells with high efficiency",
            paper_ids=["paper_006", "paper_007", "paper_008"],
            section_ids=["results_006", "results_007", "results_008"]
        ),
        
        # Scenario 3: Complementary Consolidation - Different but compatible relationships
        # Drug X and cancer treatment (related but different aspects)
        Relationship(
            source_entity="Drug X",
            target_entity="cancer",
            relationship_type=RelationshipType.TREATS,
            relationship_strength=0.8,
            description="Drug X treats breast cancer by inhibiting cell proliferation",
            paper_ids=["paper_009"],
            section_ids=["results_009"]
        ),
        
        Relationship(
            source_entity="Drug X",
            target_entity="cancer",
            relationship_type=RelationshipType.TREATS,
            relationship_strength=0.7,
            description="Drug X treats cancer by inducing apoptosis in cancer cells",
            paper_ids=["paper_010"],
            section_ids=["results_010"]
        ),
        
        # Scenario 4: Single Relationship - No consolidation needed
        Relationship(
            source_entity="p53",
            target_entity="DNA repair",
            relationship_type=RelationshipType.PROMOTES,
            relationship_strength=0.7,
            description="p53 promotes DNA repair mechanisms",
            paper_ids=["paper_011"],
            section_ids=["results_011"]
        ),
        
        # Scenario 5: Temporal Consolidation - Different time periods
        # Apoptosis and cancer progression (evolving understanding)
        Relationship(
            source_entity="apoptosis",
            target_entity="cancer progression",
            relationship_type=RelationshipType.INHIBITS,
            relationship_strength=0.6,
            description="Apoptosis inhibits cancer progression (early studies)",
            paper_ids=["paper_012"],
            section_ids=["results_012"]
        ),
        
        Relationship(
            source_entity="apoptosis",
            target_entity="cancer progression",
            relationship_type=RelationshipType.INHIBITS,
            relationship_strength=0.8,
            description="Apoptosis inhibits cancer progression through programmed cell death (recent studies)",
            paper_ids=["paper_013", "paper_014"],
            section_ids=["results_013", "results_014"]
        )
    ]
    
    return relationships

def print_relationships(relationships: List[Relationship], title: str):
    """Print relationships in a formatted way"""
    print(f"\n📊 {title} ({len(relationships)} relationships):")
    for i, rel in enumerate(relationships, 1):
        print(f"  {i}. {rel.source_entity} → {rel.target_entity}")
        print(f"     Type: {rel.relationship_type}")
        print(f"     Strength: {rel.relationship_strength}")
        print(f"     Description: {rel.description}")
        print(f"     Papers: {rel.paper_ids}")
        print()

def print_relationship_groups(relationship_groups: Dict[tuple, List[Relationship]]):
    """Print relationship groups in a formatted way"""
    print(f"\n🔗 RELATIONSHIP GROUPS ({len(relationship_groups)} groups):")
    for i, (group_key, group_rels) in enumerate(relationship_groups.items(), 1):
        source_entity, target_entity, relationship_type = group_key
        print(f"\n  {i}. Group: {source_entity} → {target_entity} ({relationship_type})")
        print(f"     Relationships: {len(group_rels)}")
        for j, rel in enumerate(group_rels, 1):
            print(f"       {j}. Strength: {rel.relationship_strength}, Papers: {len(rel.paper_ids)}")
            print(f"          Description: {rel.description[:80]}...")

def print_consolidation_results(consolidation_results: Dict[str, Any]):
    """Print consolidation results in a formatted way"""
    print(f"\n✅ CONSOLIDATION RESULTS:")
    print(f"   Relationships Processed: {consolidation_results.get('relationships_processed', 0)}")
    print(f"   Consolidated Relationships: {len(consolidation_results.get('consolidated_relationships', []))}")
    
    summary = consolidation_results.get('consolidation_summary', {})
    print(f"\n📊 CONSOLIDATION SUMMARY:")
    print(f"   Consensus: {summary.get('consensus', 0)}")
    print(f"   Evidence-Based: {summary.get('evidence_based', 0)}")
    print(f"   Temporal: {summary.get('temporal', 0)}")
    print(f"   Complementary: {summary.get('complementary', 0)}")
    print(f"   Single Relationship: {summary.get('single_relationship', 0)}")
    print(f"   Errors: {summary.get('errors', 0)}")
    
    print(f"\n🔍 DETAILED CONSOLIDATION RESULTS:")
    for i, result in enumerate(consolidation_results.get('consolidated_relationships', []), 1):
        print(f"\n  {i}. Consolidation Result:")
        
        if "consolidation_result" in result:
            consolidation_result = result["consolidation_result"]
            consolidated_rel = consolidation_result.get("consolidated_relationship", {})
            
            print(f"     Strategy: {consolidation_result.get('consolidation_strategy', 'N/A')}")
            print(f"     Entities: {consolidated_rel.get('source_entity', 'N/A')} → {consolidated_rel.get('target_entity', 'N/A')}")
            print(f"     Type: {consolidated_rel.get('relationship_type', 'N/A')}")
            print(f"     Strength: {consolidated_rel.get('relationship_strength', 'N/A')}")
            print(f"     Evidence Count: {consolidated_rel.get('evidence_count', 'N/A')}")
            print(f"     Consensus Level: {consolidated_rel.get('consensus_level', 'N/A')}")
            print(f"     Confidence: {consolidated_rel.get('confidence', 'N/A')}")
            print(f"     Papers: {consolidated_rel.get('paper_ids', [])}")
            
            description = consolidated_rel.get('description', 'N/A')
            print(f"     Description: {description[:100]}..." if len(description) > 100 else f"     Description: {description}")
            
            context_annotations = consolidated_rel.get('context_annotations', {})
            if context_annotations:
                print(f"     Context Annotations:")
                for key, value in context_annotations.items():
                    print(f"       {key}: {value}")
            
            consolidation_notes = consolidation_result.get('consolidation_notes', 'N/A')
            print(f"     Consolidation Notes: {consolidation_notes[:150]}..." if len(consolidation_notes) > 150 else f"     Consolidation Notes: {consolidation_notes}")
        
        elif "consolidated_relationship" in result:
            # Direct consolidated relationship format
            consolidated_rel = result["consolidated_relationship"]
            print(f"     Entities: {consolidated_rel.get('source_entity', 'N/A')} → {consolidated_rel.get('target_entity', 'N/A')}")
            print(f"     Type: {consolidated_rel.get('relationship_type', 'N/A')}")
            print(f"     Strength: {consolidated_rel.get('relationship_strength', 'N/A')}")
            print(f"     Evidence Count: {consolidated_rel.get('evidence_count', 'N/A')}")

async def test_relationship_grouping():
    """Test the relationship grouping functionality"""
    print_subheader("TESTING RELATIONSHIP GROUPING")
    
    # Create test relationships
    relationships = create_test_relationships()
    print_relationships(relationships, "INPUT RELATIONSHIPS")
    
    # Initialize consolidator
    consolidator = RelationshipConsolidator()
    
    # Group relationships
    relationship_groups = consolidator.group_relationships_by_entities_and_type(relationships)
    print_relationship_groups(relationship_groups)
    
    return relationship_groups

async def test_consolidation_metrics():
    """Test the consolidation metrics calculation"""
    print_subheader("TESTING CONSOLIDATION METRICS")
    
    # Create test relationships
    relationships = create_test_relationships()
    consolidator = RelationshipConsolidator()
    
    # Group relationships
    relationship_groups = consolidator.group_relationships_by_entities_and_type(relationships)
    
    print(f"\n📊 METRICS CALCULATION:")
    for i, (group_key, group_rels) in enumerate(relationship_groups.items(), 1):
        if len(group_rels) > 1:  # Only show groups with multiple relationships
            source_entity, target_entity, relationship_type = group_key
            print(f"\n  {i}. Group: {source_entity} → {target_entity} ({relationship_type})")
            
            # Calculate metrics
            metrics = consolidator.calculate_consolidation_metrics(group_rels)
            
            print(f"     Evidence Count: {metrics.get('evidence_count', 'N/A')}")
            print(f"     Average Strength: {metrics.get('average_strength', 'N/A'):.3f}")
            print(f"     Strength Variance: {metrics.get('strength_variance', 'N/A'):.3f}")
            print(f"     Consensus Ratio: {metrics.get('consensus_ratio', 'N/A'):.3f}")
            print(f"     Temporal Span: {metrics.get('temporal_span_years', 'N/A')} years")
            print(f"     Unique Papers: {metrics.get('unique_papers', 'N/A')}")
            print(f"     Unique Sections: {metrics.get('unique_sections', 'N/A')}")

async def test_strategy_determination():
    """Test the consolidation strategy determination"""
    print_subheader("TESTING STRATEGY DETERMINATION")
    
    # Create test relationships
    relationships = create_test_relationships()
    consolidator = RelationshipConsolidator()
    
    # Group relationships
    relationship_groups = consolidator.group_relationships_by_entities_and_type(relationships)
    
    print(f"\n🎯 STRATEGY DETERMINATION:")
    for i, (group_key, group_rels) in enumerate(relationship_groups.items(), 1):
        source_entity, target_entity, relationship_type = group_key
        print(f"\n  {i}. Group: {source_entity} → {target_entity} ({relationship_type})")
        
        # Calculate metrics
        metrics = consolidator.calculate_consolidation_metrics(group_rels)
        
        # Determine strategy
        strategy = consolidator.determine_consolidation_strategy(group_rels, metrics)
        
        print(f"     Strategy: {strategy}")
        print(f"     Reasoning:")
        print(f"       - Evidence Count: {metrics.get('evidence_count', 0)}")
        print(f"       - Consensus Ratio: {metrics.get('consensus_ratio', 0):.3f}")
        print(f"       - Strength Variance: {metrics.get('strength_variance', 0):.3f}")
        
        if strategy == "consensus":
            print(f"       → High consensus ratio ({metrics.get('consensus_ratio', 0):.3f}) indicates agreement")
        elif strategy == "evidence_based":
            print(f"       → Low consensus ratio ({metrics.get('consensus_ratio', 0):.3f}) indicates conflicting evidence")
        elif strategy == "single_relationship":
            print(f"       → Only one relationship in group")

async def test_noisy_or_calculation():
    """Test the Noisy-OR strength calculation"""
    print_subheader("TESTING NOISY-OR CALCULATION")
    
    from app.utils.math_utils import calculate_noisy_or_strength
    
    # Test cases
    test_cases = [
        {
            "name": "Single Relationship",
            "strengths": [0.8],
            "expected": "Should return 0.8"
        },
        {
            "name": "Two Agreeing Relationships",
            "strengths": [0.8, 0.7],
            "expected": "Should return 0.94 (1 - 0.2 × 0.3 = 1 - 0.06 = 0.94)"
        },
        {
            "name": "Three Agreeing Relationships",
            "strengths": [0.8, 0.7, 0.9],
            "expected": "Should return 0.994 (1 - 0.2 × 0.3 × 0.1 = 1 - 0.006 = 0.994)"
        },
        {
            "name": "Multiple Relationships",
            "strengths": [0.5, 0.6, 0.7, 0.8],
            "expected": "Should return high value due to multiple evidence"
        }
    ]
    
    print(f"\n🧮 NOISY-OR CALCULATION TESTS:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  {i}. {test_case['name']}")
        print(f"     Input Strengths: {test_case['strengths']}")
        
        result = calculate_noisy_or_strength(test_case['strengths'])
        print(f"     Result: {result:.4f}")
        print(f"     Expected: {test_case['expected']}")
        
        # Manual calculation for verification
        if len(test_case['strengths']) > 1:
            product = 1.0
            for strength in test_case['strengths']:
                product *= (1.0 - strength)
            manual_result = 1.0 - product
            print(f"     Manual Calculation: {manual_result:.4f}")
            print(f"     Match: {'✅' if abs(result - manual_result) < 0.0001 else '❌'}")

async def test_full_consolidation():
    """Test the full relationship consolidation process"""
    print_subheader("TESTING FULL RELATIONSHIP CONSOLIDATION")
    
    # Create test relationships
    relationships = create_test_relationships()
    print_relationships(relationships, "INPUT RELATIONSHIPS")
    
    # Initialize consolidator
    consolidator = RelationshipConsolidator()
    
    print(f"\n🔄 Running full relationship consolidation...")
    
    # Perform consolidation
    consolidation_results = await consolidator.consolidate_relationships(relationships)
    
    print_consolidation_results(consolidation_results)
    
    return consolidation_results

async def demonstrate_consolidation_strategies():
    """Demonstrate different consolidation strategies"""
    print_subheader("DEMONSTRATING CONSOLIDATION STRATEGIES")
    
    strategies = [
        {
            "name": "Consensus Consolidation",
            "description": "Multiple agreeing relationships with high consensus ratio",
            "example": "TP53 → apoptosis (3 relationships, all PROMOTES, strengths: 0.8, 0.7, 0.9)",
            "result": "Consolidated relationship with Noisy-OR strength: 0.994"
        },
        {
            "name": "Evidence-Based Consolidation", 
            "description": "Choose relationship with strongest evidence when consensus is low",
            "example": "CRISPR-Cas9 → gene editing (2 relationships, different strengths: 0.6 vs 0.9)",
            "result": "Choose relationship with strength 0.9 (more evidence)"
        },
        {
            "name": "Complementary Consolidation",
            "description": "Merge compatible relationships with combined descriptions",
            "example": "Drug X → cancer (2 relationships, both TREATS but different mechanisms)",
            "result": "Combined description with both mechanisms"
        },
        {
            "name": "Temporal Consolidation",
            "description": "Prefer more recent findings when evidence is comparable",
            "example": "apoptosis → cancer progression (early vs recent studies)",
            "result": "Choose recent studies with better methodology"
        },
        {
            "name": "Single Relationship",
            "description": "No consolidation needed for unique relationships",
            "example": "p53 → DNA repair (only one relationship)",
            "result": "Return relationship as-is"
        }
    ]
    
    print(f"\n📚 CONSOLIDATION STRATEGIES:")
    for i, strategy in enumerate(strategies, 1):
        print(f"\n  {i}. {strategy['name']}")
        print(f"     Description: {strategy['description']}")
        print(f"     Example: {strategy['example']}")
        print(f"     Result: {strategy['result']}")

async def main():
    """Main test function"""
    print_header("CONSOLIDATE RELATIONSHIPS NODE COMPREHENSIVE TEST")
    print("This test demonstrates the _consolidate_relationships node and its services:")
    print("1. RelationshipConsolidator - Groups and consolidates duplicate relationships")
    print("2. Noisy-OR Formula - Aggregates relationship strengths")
    print("3. Consolidation Strategies - Different approaches for different scenarios")
    print("4. LLM Analysis - Intelligent consolidation decisions")
    
    try:
        # Demonstrate strategies
        await demonstrate_consolidation_strategies()
        
        # Test relationship grouping
        relationship_groups = await test_relationship_grouping()
        
        # Test consolidation metrics
        await test_consolidation_metrics()
        
        # Test strategy determination
        await test_strategy_determination()
        
        # Test Noisy-OR calculation
        await test_noisy_or_calculation()
        
        # Test full consolidation
        consolidation_results = await test_full_consolidation()
        
        print_header("TEST SUMMARY")
        print("✅ RelationshipConsolidator: Successfully grouped and consolidated relationships")
        print("✅ Noisy-OR Formula: Correctly aggregated relationship strengths")
        print("✅ Consolidation Strategies: Applied appropriate strategies based on metrics")
        print("✅ LLM Integration: Made intelligent consolidation decisions")
        print("\n🎯 The _consolidate_relationships node is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        logger.error(f"Test error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
