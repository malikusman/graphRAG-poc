#!/usr/bin/env python3
"""
Test the ContradictionDetector and ContradictionResolver services
This test demonstrates how these services work together to detect and resolve conflicts
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.relationships import Relationship, RelationshipType
from app.models.entities import Entity, EntityType, EntityCategory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_entities() -> List[Entity]:
    """Create test entities for relationships"""
    return [
        Entity(
            entity_name="p53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="Tumor suppressor protein p53",
            aliases=["TP53"],
            paper_ids=["paper_001"],
            section_ids=["section_001"],
            frequency=1
        ),
        Entity(
            entity_name="MDM2",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="Mouse double minute 2 homolog",
            aliases=["murine double minute 2"],
            paper_ids=["paper_001"],
            section_ids=["section_001"],
            frequency=1
        ),
        Entity(
            entity_name="cancer",
            entity_type=EntityType.DISEASE,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="Malignant neoplastic disease",
            aliases=["tumor", "neoplasm"],
            paper_ids=["paper_001"],
            section_ids=["section_001"],
            frequency=1
        )
    ]

def create_contradictory_relationships() -> List[Relationship]:
    """Create relationships that contain contradictions"""
    return [
        # Contradiction 1: p53 and MDM2 relationship
        # Some papers say MDM2 inhibits p53, others say it activates p53
        Relationship(
            source_entity="MDM2",
            target_entity="p53",
            relationship_type=RelationshipType.INHIBITS,
            relationship_strength=0.9,
            description="MDM2 ubiquitinates and degrades p53 protein, leading to p53 inhibition and reduced tumor suppression activity. This is a well-established mechanism in cancer biology.",
            paper_ids=["paper_001", "paper_002", "paper_003"],
            section_ids=["section_001", "section_002"],
            frequency=3
        ),
        Relationship(
            source_entity="MDM2",
            target_entity="p53",
            relationship_type=RelationshipType.ACTIVATES,
            relationship_strength=0.7,
            description="Recent studies show that MDM2 can activate p53 under certain cellular stress conditions, contradicting the traditional inhibitory role.",
            paper_ids=["paper_004"],
            section_ids=["section_003"],
            frequency=1
        ),
        
        # Contradiction 2: p53 and cancer relationship
        # Some papers say p53 prevents cancer, others say it promotes cancer
        Relationship(
            source_entity="p53",
            target_entity="cancer",
            relationship_type=RelationshipType.PREVENTS,
            relationship_strength=0.95,
            description="p53 is a well-known tumor suppressor that prevents cancer development by inducing cell cycle arrest and apoptosis in response to DNA damage.",
            paper_ids=["paper_001", "paper_002", "paper_003", "paper_004", "paper_005"],
            section_ids=["section_001", "section_002", "section_003"],
            frequency=5
        ),
        Relationship(
            source_entity="p53",
            target_entity="cancer",
            relationship_type=RelationshipType.PROMOTES,
            relationship_strength=0.6,
            description="Mutant p53 can gain oncogenic functions and promote cancer progression, especially in advanced tumors.",
            paper_ids=["paper_006"],
            section_ids=["section_004"],
            frequency=1
        ),
        
        # No contradiction: MDM2 and cancer (consistent relationship)
        Relationship(
            source_entity="MDM2",
            target_entity="cancer",
            relationship_type=RelationshipType.PROMOTES,
            relationship_strength=0.8,
            description="MDM2 overexpression promotes cancer by inhibiting p53 tumor suppressor function.",
            paper_ids=["paper_001", "paper_002"],
            section_ids=["section_001"],
            frequency=2
        )
    ]

def print_relationships(relationships: List[Relationship], title: str):
    """Print relationships in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(relationships)}")
    for i, rel in enumerate(relationships, 1):
        print(f"   {i}. {rel.source_entity} --[{rel.relationship_type}]--> {rel.target_entity}")
        print(f"      Strength: {rel.relationship_strength}")
        print(f"      Description: {rel.description[:100]}...")
        print(f"      Papers: {len(rel.paper_ids)} | Sections: {len(rel.section_ids)} | Frequency: {rel.frequency}")
        print()

def print_contradictions(contradictions: List[Dict[str, Any]], title: str):
    """Print contradictions in a formatted way"""
    print(f"\n🚨 {title}:")
    print(f"   Count: {len(contradictions)}")
    for i, contradiction in enumerate(contradictions, 1):
        print(f"   {i}. Contradiction ID: {contradiction.get('contradiction_id', 'Unknown')}")
        print(f"      Type: {contradiction.get('contradiction_type', 'Unknown')}")
        print(f"      Severity: {contradiction.get('severity', 'Unknown')}")
        print(f"      Entity Pair: {contradiction.get('entity_pair', [])}")
        print(f"      Description: {contradiction.get('description', 'No description')}")
        
        contradicting_rels = contradiction.get('contradicting_relationships', [])
        print(f"      Contradicting Relationships: {len(contradicting_rels)}")
        for j, rel in enumerate(contradicting_rels, 1):
            print(f"         {j}. {rel.get('source_entity')} --[{rel.get('relationship_type')}]--> {rel.get('target_entity')}")
            print(f"            Strength: {rel.get('evidence_strength', 0.0)}")
        print()

def print_resolutions(resolutions: List[Dict[str, Any]], title: str):
    """Print resolutions in a formatted way"""
    print(f"\n✅ {title}:")
    print(f"   Count: {len(resolutions)}")
    for i, resolution in enumerate(resolutions, 1):
        print(f"   {i}. Resolution Type: {resolution.get('resolution', 'Unknown')}")
        print(f"      Confidence: {resolution.get('confidence', 0.0)}")
        print(f"      Reasoning: {resolution.get('reasoning', 'No reasoning provided')}")
        
        chosen_rel = resolution.get('chosen_relationship')
        if chosen_rel:
            print(f"      Chosen: {chosen_rel.get('source_entity')} --[{chosen_rel.get('relationship_type')}]--> {chosen_rel.get('target_entity')}")
        
        rejected_rels = resolution.get('rejected_relationships', [])
        if rejected_rels:
            print(f"      Rejected: {len(rejected_rels)} relationships")
            for j, rel in enumerate(rejected_rels, 1):
                print(f"         {j}. {rel.get('source_entity')} --[{rel.get('relationship_type')}]--> {rel.get('target_entity')}")
        print()

async def test_contradiction_detector():
    """Test the ContradictionDetector service"""
    print("🔍 Testing ContradictionDetector Service")
    print("=" * 60)
    
    try:
        from app.services.contradiction_detector import ContradictionDetector
        print("✅ ContradictionDetector imported successfully")
        
        detector = ContradictionDetector()
        print("✅ ContradictionDetector service created successfully")
        
        # Create test relationships with contradictions
        relationships = create_contradictory_relationships()
        print(f"📄 Created {len(relationships)} test relationships")
        
        print_relationships(relationships, "Input Relationships (With Expected Contradictions)")
        
        print("🎯 Expected Contradictions:")
        print("   📌 MDM2-p53: INHIBITS vs ACTIVATES (should be detected)")
        print("   📌 p53-cancer: PREVENTS vs PROMOTES (should be detected)")
        print("   📌 MDM2-cancer: Only PROMOTES (no contradiction expected)")
        
        # Test contradiction detection
        print("\n🔍 Detecting contradictions...")
        contradictions = await detector.detect_relationship_contradictions_with_context(
            relationships, context_info={"test_mode": True}
        )
        
        print_contradictions(contradictions, "Detected Contradictions")
        
        # Test evidence strength analysis
        print("\n🔍 Testing evidence strength analysis...")
        for rel in relationships[:2]:  # Test first 2 relationships
            evidence_strength = await detector.analyze_evidence_strength(rel)
            print(f"   📌 {rel.source_entity} --[{rel.relationship_type}]--> {rel.target_entity}")
            print(f"      Evidence Strength: {evidence_strength:.3f}")
            print(f"      Factors: strength={rel.relationship_strength}, papers={len(rel.paper_ids)}, sections={len(rel.section_ids)}")
        
        return contradictions
        
    except Exception as e:
        print(f"❌ ContradictionDetector test failed: {str(e)}")
        logger.error(f"ContradictionDetector test failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

async def test_contradiction_resolver(contradictions: List[Dict[str, Any]]):
    """Test the ContradictionResolver service"""
    print("\n🔧 Testing ContradictionResolver Service")
    print("=" * 60)
    
    try:
        from app.services.contradiction_resolver import ContradictionResolver
        print("✅ ContradictionResolver imported successfully")
        
        resolver = ContradictionResolver()
        print("✅ ContradictionResolver service created successfully")
        
        if not contradictions:
            print("❌ No contradictions to resolve")
            return []
        
        resolutions = []
        
        # Test each contradiction resolution strategy
        for i, contradiction in enumerate(contradictions, 1):
            print(f"\n🔍 Resolving Contradiction {i}: {contradiction.get('contradiction_id', 'Unknown')}")
            
            # Determine resolution strategy
            strategy = resolver.determine_resolution_strategy(contradiction)
            print(f"   📌 Strategy: {strategy}")
            
            # Apply the appropriate resolution method
            if strategy == "evidence_based":
                resolution = resolver.resolve_evidence_based(contradiction)
                print(f"   📌 Evidence-based resolution applied")
            elif strategy == "consensus_based":
                resolution = resolver.resolve_consensus_based(contradiction)
                print(f"   📌 Consensus-based resolution applied")
            elif strategy == "context_dependent":
                resolution = await resolver.resolve_context_dependent(contradiction)
                print(f"   📌 Context-dependent resolution applied")
            else:
                resolution = {"resolution": "manual_review", "confidence": 0.0, "reasoning": "Requires manual review"}
                print(f"   📌 Manual review required")
            
            resolution["contradiction_id"] = contradiction.get("contradiction_id", f"contradiction_{i}")
            resolutions.append(resolution)
            
            print(f"   📌 Resolution: {resolution.get('resolution', 'Unknown')}")
            print(f"   📌 Confidence: {resolution.get('confidence', 0.0)}")
            print(f"   📌 Reasoning: {resolution.get('reasoning', 'No reasoning')}")
        
        print_resolutions(resolutions, "Contradiction Resolutions")
        
        # Test individual resolution methods
        print("\n🔍 Testing individual resolution methods...")
        
        if contradictions:
            test_contradiction = contradictions[0]
            
            # Test evidence-based resolution
            evidence_resolution = resolver.resolve_evidence_based(test_contradiction)
            print(f"   📌 Evidence-based: {evidence_resolution.get('resolution', 'Unknown')} (confidence: {evidence_resolution.get('confidence', 0.0)})")
            
            # Test consensus-based resolution
            consensus_resolution = resolver.resolve_consensus_based(test_contradiction)
            print(f"   📌 Consensus-based: {consensus_resolution.get('resolution', 'Unknown')} (confidence: {consensus_resolution.get('confidence', 0.0)})")
            
            # Test context-dependent resolution (async)
            context_resolution = await resolver.resolve_context_dependent(test_contradiction)
            print(f"   📌 Context-dependent: {context_resolution.get('resolution', 'Unknown')} (confidence: {context_resolution.get('confidence', 0.0)})")
        
        return resolutions
        
    except Exception as e:
        print(f"❌ ContradictionResolver test failed: {str(e)}")
        logger.error(f"ContradictionResolver test failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

async def test_contradiction_services():
    """Test both ContradictionDetector and ContradictionResolver services"""
    print("🚀 Starting Contradiction Services Test")
    print("=" * 80)
    
    print("🎯 Goal: Demonstrate how ContradictionDetector finds conflicts and ContradictionResolver fixes them")
    print("📚 Context: Scientific papers often contain contradictory information that needs to be resolved")
    
    # Test ContradictionDetector
    contradictions = await test_contradiction_detector()
    
    # Test ContradictionResolver
    resolutions = await test_contradiction_resolver(contradictions)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 80)
    print(f"📈 Contradictions Detected: {len(contradictions)}")
    print(f"📈 Contradictions Resolved: {len(resolutions)}")
    
    if contradictions and resolutions:
        print(f"\n🎉 SUCCESS: Contradiction detection and resolution pipeline is working!")
        print(f"📌 The system can identify conflicting information and resolve it using evidence-based strategies")
    elif contradictions:
        print(f"\n⚠️  PARTIAL: Contradictions detected but resolution had issues")
    else:
        print(f"\n❌ ISSUE: No contradictions were detected (this might indicate a problem)")
    
    print("\n🔍 Key Insights:")
    print("   📌 ContradictionDetector uses LLM to identify semantic conflicts between relationships")
    print("   📌 ContradictionResolver uses multiple strategies (evidence, consensus, context) to resolve conflicts")
    print("   📌 Evidence strength considers relationship strength, paper count, section count, and description quality")
    print("   📌 The system can handle complex scientific contradictions automatically")

if __name__ == "__main__":
    asyncio.run(test_contradiction_services())
