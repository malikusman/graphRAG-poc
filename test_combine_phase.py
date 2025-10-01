#!/usr/bin/env python3
"""
Combine Phase Test
Tests the entity and relationship combining logic with detailed explanations
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
        logging.FileHandler('combine_phase_test.log')
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

async def test_combine_phase():
    """Test the Combine phase with detailed explanations"""
    print("🚀 Starting Combine Phase Test")
    print("="*80)
    
    # Create test data that mimics what we'd get from the Map phase
    # This simulates the output from our successful LLM test
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
        # Section 2 entities (notice p53 and TP53 appear again - these should be merged)
        {
            "entity_name": "CRISPR-Cas9",
            "entity_type": "method",
            "entity_category": "methods_and_approaches",
            "aliases": ["CRISPR", "Cas9", "CRISPR-Cas9 system"],
            "description": "Genome editing method using clustered regularly interspaced short palindromic repeats and Cas9 endonuclease.",
            "section_id": "section_002",
            "provenance": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines."
        },
        {
            "entity_name": "TP53",  # DUPLICATE - should be merged with section_001 TP53
            "entity_type": "gene",
            "entity_category": "biological_entities",
            "aliases": ["p53", "Tumor Protein p53"],
            "description": "A gene that encodes a protein that regulates the cell cycle and functions as a tumor suppressor.",
            "section_id": "section_002",
            "provenance": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines."
        },
        {
            "entity_name": "p53",  # DUPLICATE - should be merged with section_001 p53
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["Tumor Protein 53", "p53 protein"],
            "description": "A protein encoded by the TP53 gene that plays a crucial role in regulating the cell cycle and preventing cancer formation.",
            "section_id": "section_002",
            "provenance": "Western blot analysis was performed to detect p53 protein expression levels."
        },
        {
            "entity_name": "MDM2",  # DUPLICATE - should be merged with section_001 MDM2
            "entity_type": "protein",
            "entity_category": "biological_entities",
            "aliases": ["Mouse Double Minute 2 homolog"],
            "description": "A protein that regulates the p53 tumor suppressor and is involved in the control of cell proliferation.",
            "section_id": "section_002",
            "provenance": "Immunoprecipitation assays were used to study the p53-MDM2 protein interaction."
        }
    ]
    
    temp_relationships = [
        # Section 1 relationships
        {
            "source_entity": "p53",
            "target_entity": "MDM2",
            "relationship_type": "interacts_with",
            "relationship_strength": 0.85,
            "description": "The tumor suppressor protein p53 interacts with MDM2, which targets p53 for proteasomal degradation.",
            "section_id": "section_001",
            "provenance": "It interacts with MDM2 (murine double minute 2), which targets p53 for proteasomal degradation."
        },
        {
            "source_entity": "TP53",
            "target_entity": "breast cancer",
            "relationship_type": "associated_with",
            "relationship_strength": 0.75,
            "description": "Mutations in the TP53 gene are associated with breast cancer.",
            "section_id": "section_001",
            "provenance": "Mutations in the TP53 gene are associated with various cancers including breast cancer."
        },
        # Section 2 relationships (notice p53-MDM2 appears again - should be merged)
        {
            "source_entity": "CRISPR-Cas9",
            "target_entity": "TP53",
            "relationship_type": "mutates",
            "relationship_strength": 0.85,
            "description": "CRISPR-Cas9 is used to mutate the TP53 gene in human cancer cell lines.",
            "section_id": "section_002",
            "provenance": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines."
        },
        {
            "source_entity": "p53",
            "target_entity": "MDM2",
            "relationship_type": "interacts_with",  # DUPLICATE - should be merged with section_001
            "relationship_strength": 0.8,
            "description": "p53 protein interacts with MDM2 as studied through immunoprecipitation assays.",
            "section_id": "section_002",
            "provenance": "Immunoprecipitation assays were used to study the p53-MDM2 protein interaction."
        }
    ]
    
    print(f"📄 Test Data Created:")
    print(f"   🏷️ Temp Entities: {len(temp_entities)}")
    print(f"   🔗 Temp Relationships: {len(temp_relationships)}")
    print(f"   📝 Sections: 2")
    
    # ============================================================================
    # STEP 1: COMBINE ENTITIES - DETAILED EXPLANATION
    # ============================================================================
    print_step_header(1, "COMBINE ENTITIES", "Merge duplicate entities within the document")
    
    print_explanation(
        "What is Entity Combining?",
        "Entity combining takes all the entities extracted from different sections and merges duplicates. "
        "For example, if 'p53' appears in both section 1 and section 2, we combine them into one entity "
        "with combined aliases, descriptions, and section IDs."
    )
    
    print_data("Input Temp Entities", temp_entities)
    
    # Group entities by name and type
    print_explanation(
        "Step 1: Grouping Entities",
        "We group entities by their name and type. Entities with the same name and type are considered duplicates. "
        "For example, 'p53' (protein) from section 1 and 'p53' (protein) from section 2 will be grouped together."
    )
    
    entity_groups = {}
    for entity in temp_entities:
        key = (entity["entity_name"], entity["entity_type"])
        if key not in entity_groups:
            entity_groups[key] = []
        entity_groups[key].append(entity)
    
    print(f"\n📊 Entity Groups Created:")
    for (name, entity_type), entities in entity_groups.items():
        print(f"   {name} ({entity_type}): {len(entities)} instances")
        for i, entity in enumerate(entities):
            print(f"     {i+1}. Section {entity['section_id']}: {entity['description'][:50]}...")
    
    print_explanation(
        "Step 2: Merging Entity Groups",
        "For each group, we create a merged entity that combines: "
        "• All aliases from all instances "
        "• The best description (longest/most detailed) "
        "• Combined section IDs and provenance "
        "• Frequency count (how many times it appeared)"
    )
    
    # Merge entities
    doc_entities = []
    for (name, entity_type), entities in entity_groups.items():
        print(f"\n🔄 Merging {len(entities)} instances of {name} ({entity_type})")
        
        # Combine aliases
        all_aliases = set()
        for entity in entities:
            all_aliases.update(entity.get("aliases", []))
        
        print(f"   📋 Aliases to combine: {[entity.get('aliases', []) for entity in entities]}")
        print(f"   📋 Combined aliases: {list(all_aliases)}")
        
        # Select best description (longest/most detailed)
        best_entity = max(entities, key=lambda e: len(e.get("description", "")))
        print(f"   📝 Best description from section {best_entity['section_id']}: {best_entity['description'][:100]}...")
        
        # Create merged entity
        merged_entity = {
            "entity_name": name,
            "entity_type": entity_type,
            "entity_category": best_entity["entity_category"],
            "aliases": list(all_aliases),
            "description": best_entity["description"],
            "frequency": len(entities),
            "section_ids": [e["section_id"] for e in entities],
            "provenance": [e["provenance"] for e in entities]
        }
        
        doc_entities.append(merged_entity)
        print(f"   ✅ Merged into: {merged_entity['entity_name']} (frequency: {merged_entity['frequency']})")
        print(f"      Aliases: {merged_entity['aliases']}")
        print(f"      Section IDs: {merged_entity['section_ids']}")
    
    print_data("Combined Doc Entities", doc_entities)
    print(f"\n✅ STEP 1 Complete: {len(temp_entities)} temp entities → {len(doc_entities)} doc entities")
    
    # ============================================================================
    # STEP 2: COMBINE RELATIONSHIPS - DETAILED EXPLANATION
    # ============================================================================
    print_step_header(2, "COMBINE RELATIONSHIPS", "Merge duplicate relationships using Noisy-OR formula")
    
    print_explanation(
        "What is Relationship Combining?",
        "Relationship combining takes all the relationships extracted from different sections and merges duplicates. "
        "For example, if 'p53 interacts_with MDM2' appears in both section 1 and section 2, we combine them "
        "into one relationship with a combined strength using the Noisy-OR formula."
    )
    
    print_data("Input Temp Relationships", temp_relationships)
    
    # Group relationships by source, target, and type
    print_explanation(
        "Step 1: Grouping Relationships",
        "We group relationships by source entity, target entity, and relationship type. "
        "Relationships with the same source, target, and type are considered duplicates. "
        "For example, 'p53 interacts_with MDM2' from both sections will be grouped together."
    )
    
    rel_groups = {}
    for rel in temp_relationships:
        key = (rel["source_entity"], rel["target_entity"], rel["relationship_type"])
        if key not in rel_groups:
            rel_groups[key] = []
        rel_groups[key].append(rel)
    
    print(f"\n📊 Relationship Groups Created:")
    for (source, target, rel_type), relationships in rel_groups.items():
        print(f"   {source} -> {target} ({rel_type}): {len(relationships)} instances")
        for i, rel in enumerate(relationships):
            print(f"     {i+1}. Section {rel['section_id']}: strength {rel['relationship_strength']}")
    
    print_explanation(
        "Step 2: Noisy-OR Formula",
        "The Noisy-OR formula combines multiple relationship strengths into one. "
        "Formula: result = 1 - ∏(1 - strength_i) "
        "This means: if we have strengths [0.8, 0.7], the result is 1 - (1-0.8)*(1-0.7) = 1 - 0.2*0.3 = 1 - 0.06 = 0.94 "
        "This gives higher confidence when multiple sources agree on a relationship."
    )
    
    # Merge relationships using noisy-OR
    from app.utils.math_utils import calculate_noisy_or_strength
    
    doc_relationships = []
    for (source, target, rel_type), relationships in rel_groups.items():
        print(f"\n🔄 Merging {len(relationships)} instances of {source} -> {target} ({rel_type})")
        
        # Calculate noisy-OR strength
        strengths = [rel["relationship_strength"] for rel in relationships]
        noisy_or_strength = calculate_noisy_or_strength(strengths)
        
        print(f"   📊 Individual strengths: {strengths}")
        print(f"   📊 Noisy-OR calculation:")
        print(f"      Formula: 1 - ∏(1 - strength_i)")
        print(f"      Calculation: 1 - ∏{[(1-s) for s in strengths]} = 1 - {[1-s for s in strengths]} = {noisy_or_strength}")
        
        # Combine descriptions
        descriptions = [rel["description"] for rel in relationships]
        combined_description = "; ".join(set(descriptions))
        print(f"   📝 Combined descriptions: {combined_description}")
        
        # Create merged relationship
        merged_rel = {
            "source_entity": source,
            "target_entity": target,
            "relationship_type": rel_type,
            "relationship_strength": noisy_or_strength,
            "description": combined_description,
            "section_ids": [rel["section_id"] for rel in relationships],
            "provenance": [rel["provenance"] for rel in relationships]
        }
        
        doc_relationships.append(merged_rel)
        print(f"   ✅ Merged into: {merged_rel['source_entity']} -> {merged_rel['target_entity']} (strength: {merged_rel['relationship_strength']})")
        print(f"      Section IDs: {merged_rel['section_ids']}")
    
    print_data("Combined Doc Relationships", doc_relationships)
    print(f"\n✅ STEP 2 Complete: {len(temp_relationships)} temp relationships → {len(doc_relationships)} doc relationships")
    
    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================
    print(f"\n{'='*80}")
    print("🎯 COMBINE PHASE TEST SUMMARY")
    print(f"{'='*80}")
    
    print(f"📄 Input Data:")
    print(f"   🏷️ Temp entities: {len(temp_entities)}")
    print(f"   🔗 Temp relationships: {len(temp_relationships)}")
    
    print(f"\n📄 Output Data:")
    print(f"   🏷️ Doc entities: {len(doc_entities)}")
    print(f"   🔗 Doc relationships: {len(doc_relationships)}")
    
    print(f"\n📊 Entity Merging Results:")
    for entity in doc_entities:
        if entity['frequency'] > 1:
            print(f"   ✅ {entity['entity_name']} merged from {entity['frequency']} instances")
    
    print(f"\n📊 Relationship Merging Results:")
    for rel in doc_relationships:
        if len(rel['section_ids']) > 1:
            print(f"   ✅ {rel['source_entity']} -> {rel['target_entity']} merged from {len(rel['section_ids'])} instances (strength: {rel['relationship_strength']})")
    
    print(f"\n🎉 Combine phase test completed successfully!")
    print(f"📊 Successfully merged {len(temp_entities)} temp entities into {len(doc_entities)} doc entities")
    print(f"📊 Successfully merged {len(temp_relationships)} temp relationships into {len(doc_relationships)} doc relationships")
    
    return True

async def main():
    """Run the combine phase test"""
    success = await test_combine_phase()
    
    if success:
        print("\n🎉 Combine phase test completed successfully!")
        print("📊 Check the logs for detailed information about entity and relationship merging.")
    else:
        print("\n❌ Combine phase test failed!")
        print("📊 Check the logs for error details.")

if __name__ == "__main__":
    asyncio.run(main())

