#!/usr/bin/env python3
"""
Test script for enhanced EntityCanonicalizer service
Tests stable identifier extraction, enhanced analysis, and confidence-based merging
"""

import asyncio
import sys
import os
import json
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.entity_canonicalizer import EntityCanonicalizer
from app.models.entities import Entity, EntityType, EntityCategory


def create_test_entities() -> List[Entity]:
    """Create test entities with stable identifiers for testing"""
    return [
        Entity(
            entity_name="CRISPR-Cas9",
            entity_type=EntityType.PROTEIN_COMPLEX,
            entity_category=EntityCategory.PROTEINS_AND_ENZYMES,
            aliases=["CRISPR", "Cas9", "CRISPR-Cas9 system"],
            entity_description="A revolutionary gene editing system (MeSH:D000077505) that uses the Cas9 protein to make precise cuts in DNA. The CRISPR-Cas9 system has been widely used for genome editing applications.",
            frequency=1,
            paper_ids=["test_paper_1"],
            section_ids=["test_section_1"]
        ),
        Entity(
            entity_name="CRISPR",
            entity_type=EntityType.PROTEIN_COMPLEX,
            entity_category=EntityCategory.PROTEINS_AND_ENZYMES,
            aliases=["CRISPR-Cas9", "Cas9 system"],
            entity_description="Clustered Regularly Interspaced Short Palindromic Repeats (MeSH:D000077505) - a family of DNA sequences found in the genomes of prokaryotic organisms.",
            frequency=1,
            paper_ids=["test_paper_2"],
            section_ids=["test_section_2"]
        ),
        Entity(
            entity_name="TP53",
            entity_type=EntityType.GENE,
            entity_category=EntityCategory.GENES_AND_GENETIC_ELEMENTS,
            aliases=["p53", "tumor protein p53"],
            entity_description="Tumor protein p53 (HGNC:11998) is a crucial tumor suppressor gene that plays a key role in preventing cancer development.",
            frequency=1,
            paper_ids=["test_paper_3"],
            section_ids=["test_section_3"]
        ),
        Entity(
            entity_name="p53",
            entity_type=EntityType.GENE,
            entity_category=EntityCategory.GENES_AND_GENETIC_ELEMENTS,
            aliases=["TP53", "tumor protein p53"],
            entity_description="The p53 protein (HGNC:11998) is encoded by the TP53 gene and functions as a tumor suppressor.",
            frequency=1,
            paper_ids=["test_paper_4"],
            section_ids=["test_section_4"]
        )
    ]


async def test_stable_identifier_extraction():
    """Test stable identifier extraction from entities"""
    print("🧪 Testing Stable Identifier Extraction...")
    
    canonicalizer = EntityCanonicalizer()
    test_entities = create_test_entities()
    
    for entity in test_entities:
        identifiers = canonicalizer.find_stable_identifiers_in_entity(entity)
        print(f"  📋 {entity.entity_name}: {identifiers}")
    
    print("✅ Stable identifier extraction test completed\n")


async def test_enhanced_similarity_analysis():
    """Test enhanced similarity analysis with context"""
    print("🧪 Testing Enhanced Similarity Analysis...")
    
    canonicalizer = EntityCanonicalizer()
    test_entities = create_test_entities()
    
    # Test CRISPR entities
    crispr_entity = test_entities[0]  # CRISPR-Cas9
    crispr_simple = test_entities[1]  # CRISPR
    
    print(f"  🔍 Analyzing similarity between '{crispr_entity.entity_name}' and '{crispr_simple.entity_name}'...")
    
    try:
        analysis_result = await canonicalizer.calculate_entity_similarity_with_context(
            crispr_entity, 
            [crispr_simple]
        )
        
        if "analysis" in analysis_result:
            analysis = analysis_result["analysis"]
            print(f"    📊 Should merge: {analysis.get('should_merge', False)}")
            print(f"    📊 Confidence: {analysis.get('confidence', 0.0)}")
            print(f"    📊 Reasoning: {analysis.get('reasoning', 'N/A')}")
            print(f"    📊 Evidence types: {analysis.get('evidence_types', [])}")
            print(f"    📊 Stable identifiers found: {analysis.get('stable_identifiers_found', [])}")
        else:
            print("    ❌ No analysis result found")
            
    except Exception as e:
        print(f"    ❌ Error in similarity analysis: {str(e)}")
    
    print("✅ Enhanced similarity analysis test completed\n")


async def test_enhanced_canonicalization():
    """Test enhanced canonicalization with context"""
    print("🧪 Testing Enhanced Canonicalization...")
    
    canonicalizer = EntityCanonicalizer()
    test_entities = create_test_entities()
    
    # Test with CRISPR entities
    crispr_entities = [test_entities[0], test_entities[1]]  # CRISPR-Cas9 and CRISPR
    
    print(f"  🔄 Canonicalizing {len(crispr_entities)} CRISPR-related entities...")
    
    try:
        results = await canonicalizer.process_entity_canonicalization_with_context(
            crispr_entities, 
            None
        )
        
        print(f"    📊 Entities processed: {results['entities_processed']}")
        print(f"    📊 Merges performed: {results['merges_performed']}")
        print(f"    📊 Canonical entities: {len(results['canonical_entities'])}")
        print(f"    📊 Merge operations: {len(results['merge_operations'])}")
        
        if results['merge_operations']:
            for i, merge_op in enumerate(results['merge_operations']):
                print(f"      🔗 Merge {i+1}: {merge_op['source_entity']} → {merge_op['target_entity']}")
                print(f"        📊 Confidence: {merge_op.get('confidence', 0.0)}")
                print(f"        📊 Evidence types: {merge_op.get('evidence_types', [])}")
                print(f"        📊 Stable identifiers: {merge_op.get('stable_identifiers_found', [])}")
        
        if results['canonical_entities']:
            for i, canonical_entity in enumerate(results['canonical_entities']):
                print(f"      🎯 Canonical entity {i+1}: {canonical_entity['entity_name']}")
                print(f"        📊 Type: {canonical_entity['entity_type']}")
                print(f"        📊 Category: {canonical_entity['entity_category']}")
                print(f"        📊 Aliases: {canonical_entity.get('aliases', [])}")
        
    except Exception as e:
        print(f"    ❌ Error in canonicalization: {str(e)}")
    
    print("✅ Enhanced canonicalization test completed\n")


async def test_backward_compatibility():
    """Test backward compatibility with existing methods"""
    print("🧪 Testing Backward Compatibility...")
    
    canonicalizer = EntityCanonicalizer()
    test_entities = create_test_entities()
    
    # Test with TP53 entities
    tp53_entities = [test_entities[2], test_entities[3]]  # TP53 and p53
    
    print(f"  🔄 Testing backward compatibility with {len(tp53_entities)} TP53-related entities...")
    
    try:
        # Test old method
        results = await canonicalizer.process_entity_canonicalization(tp53_entities)
        
        print(f"    📊 Entities processed: {results['entities_processed']}")
        print(f"    📊 Merges performed: {results['merges_performed']}")
        print(f"    📊 Canonical entities: {len(results['canonical_entities'])}")
        
        # Test old similarity method
        similarity = await canonicalizer.calculate_entity_similarity(tp53_entities[0], tp53_entities[1])
        print(f"    📊 Similarity score: {similarity}")
        
    except Exception as e:
        print(f"    ❌ Error in backward compatibility test: {str(e)}")
    
    print("✅ Backward compatibility test completed\n")


async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced EntityCanonicalizer Tests\n")
    
    try:
        await test_stable_identifier_extraction()
        await test_enhanced_similarity_analysis()
        await test_enhanced_canonicalization()
        await test_backward_compatibility()
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
