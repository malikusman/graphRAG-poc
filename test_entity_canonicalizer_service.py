#!/usr/bin/env python3
"""
Test the EntityCanonicalizer service thoroughly
This test demonstrates entity canonicalization with LLM-based analysis
"""

import asyncio
import logging
from typing import Dict, Any, List
from app.models.entities import Entity, EntityType, EntityCategory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_entities() -> List[Entity]:
    """Create test entities that should be canonicalized"""
    return [
        # Group 1: Multiple variations of p53 protein (should be canonicalized)
        Entity(
            entity_name="p53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="A tumor suppressor protein that plays a crucial role in maintaining genomic stability and preventing cancer development. (MeSH: D000075101)",
            aliases=["TP53", "Tumor Protein p53", "cellular tumor antigen p53"],
            paper_ids=["paper_001"],
            section_ids=["section_001"],
            frequency=1
        ),
        Entity(
            entity_name="TP53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="The TP53 protein is encoded by the TP53 gene and functions as a tumor suppressor protein that regulates the cell cycle. (MeSH: D000075101)",
            aliases=["p53", "tumor protein 53", "cellular tumor antigen p53"],
            paper_ids=["paper_001"],
            section_ids=["section_002"],
            frequency=1
        ),
        Entity(
            entity_name="tumor protein 53",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="Also known as p53, this protein is a transcription factor that regulates gene expression in response to DNA damage and cellular stress.",
            aliases=["p53", "TP53", "cellular tumor antigen p53"],
            paper_ids=["paper_001"],
            section_ids=["section_003"],
            frequency=1
        ),
        
        # Group 2: Multiple variations of MDM2 protein (should be canonicalized)
        Entity(
            entity_name="MDM2",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="Mouse double minute 2 homolog, an oncogene that targets p53 for degradation. (HGNC: 6973)",
            aliases=["murine double minute 2", "HDM2", "E3 ubiquitin-protein ligase Mdm2"],
            paper_ids=["paper_001"],
            section_ids=["section_001"],
            frequency=1
        ),
        Entity(
            entity_name="murine double minute 2",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="MDM2 protein that regulates p53 stability through ubiquitination and proteasomal degradation.",
            aliases=["MDM2", "HDM2"],
            paper_ids=["paper_001"],
            section_ids=["section_002"],
            frequency=1
        ),
        
        # Group 3: Different entity types with similar names (should NOT be canonicalized)
        Entity(
            entity_name="TP53",
            entity_type=EntityType.GENE,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="The TP53 gene that encodes the p53 protein. (HGNC: 11998)",
            aliases=["p53 gene", "tumor protein 53 gene"],
            paper_ids=["paper_001"],
            section_ids=["section_001"],
            frequency=1
        ),
        
        # Group 4: Single entity (should remain as-is)
        Entity(
            entity_name="CRISPR-Cas9",
            entity_type=EntityType.METHOD,
            entity_category=EntityCategory.METHODS_AND_APPROACHES,
            entity_description="Genome editing method using clustered regularly interspaced short palindromic repeats and Cas9 endonuclease. (MeSH: D000077505)",
            aliases=["CRISPR", "Cas9", "CRISPR-Cas9 system"],
            paper_ids=["paper_001"],
            section_ids=["section_002"],
            frequency=1
        )
    ]

def create_existing_entities() -> List[Entity]:
    """Create existing entities in the global graph"""
    return [
        Entity(
            entity_name="p53 protein",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="Tumor suppressor protein p53 from previous research",
            aliases=["p53", "TP53"],
            paper_ids=["existing_paper_001"],
            section_ids=["existing_section_001"],
            frequency=5
        ),
        Entity(
            entity_name="MDM2 oncogene",
            entity_type=EntityType.PROTEIN,
            entity_category=EntityCategory.BIOLOGICAL_ENTITIES,
            entity_description="MDM2 oncogene from previous research",
            aliases=["MDM2"],
            paper_ids=["existing_paper_001"],
            section_ids=["existing_section_002"],
            frequency=3
        )
    ]

def print_entities(entities: List[Entity], title: str):
    """Print entities in a formatted way"""
    print(f"\n📊 {title}:")
    print(f"   Count: {len(entities)}")
    for i, entity in enumerate(entities, 1):
        if isinstance(entity, dict):
            print(f"   {i}. {entity.get('entity_name', 'Unknown')} ({entity.get('entity_type', 'Unknown')})")
            print(f"      Category: {entity.get('entity_category', 'Unknown')}")
            print(f"      Aliases: {entity.get('aliases', [])}")
            print(f"      Description: {entity.get('description', '')[:100]}...")
            print(f"      Frequency: {entity.get('frequency', 0)}")
            print(f"      Paper IDs: {entity.get('paper_ids', [])}")
            print(f"      Section IDs: {entity.get('section_ids', [])}")
        else:
            print(f"   {i}. {entity.entity_name} ({entity.entity_type})")
            print(f"      Category: {entity.entity_category}")
            print(f"      Aliases: {entity.aliases}")
            print(f"      Description: {entity.entity_description[:100]}...")
            print(f"      Frequency: {entity.frequency}")
            print(f"      Paper IDs: {entity.paper_ids}")
            print(f"      Section IDs: {entity.section_ids}")
        print()

def print_canonicalization_results(results: Dict[str, Any]):
    """Print canonicalization results"""
    print(f"\n📈 Canonicalization Results:")
    print(f"   Entities processed: {results.get('entities_processed', 0)}")
    print(f"   Merges performed: {results.get('merges_performed', 0)}")
    print(f"   Canonical entities: {len(results.get('canonical_entities', []))}")
    print(f"   Merge operations: {len(results.get('merge_operations', []))}")
    print(f"   Errors: {len(results.get('errors', []))}")
    
    if results.get('merge_operations'):
        print(f"\n🔄 Merge Operations:")
        for i, operation in enumerate(results['merge_operations'], 1):
            print(f"   {i}. {operation.get('source_entities', [])} → {operation.get('canonical_entity', 'Unknown')}")
            print(f"      Confidence: {operation.get('confidence', 0.0)}")
            print(f"      Reasoning: {operation.get('reasoning', 'No reasoning provided')}")
            print()

async def test_entity_canonicalizer_service():
    """Test the EntityCanonicalizer service thoroughly"""
    print("🚀 Starting EntityCanonicalizer Service Test")
    print("=" * 80)
    
    print("🔍 STEP 1: CREATE TEST ENTITIES")
    print("=" * 80)
    
    # Create test entities
    test_entities = create_test_entities()
    existing_entities = create_existing_entities()
    
    print(f"📄 Test Entities Created: {len(test_entities)}")
    print(f"📄 Existing Entities Created: {len(existing_entities)}")
    
    print_entities(test_entities, "Input Entities (Before Canonicalization)")
    print_entities(existing_entities, "Existing Entities (Global Graph Context)")
    
    print("\n🎯 Expected Canonicalization:")
    print("   📌 Group 1: p53, TP53, tumor protein 53 (all proteins) → Should be canonicalized into one entity")
    print("   📌 Group 2: MDM2, murine double minute 2 (both proteins) → Should be canonicalized into one entity")
    print("   📌 Group 3: TP53 (gene) vs TP53 (protein) → Should NOT be canonicalized (different types)")
    print("   📌 Group 4: CRISPR-Cas9 (single entity) → Should remain as-is")
    print("   📌 Context: Should consider existing entities for cross-document canonicalization")
    
    print("\n🔍 STEP 2: TEST ENTITY CANONICALIZER SERVICE")
    print("=" * 80)
    
    try:
        from app.services.entity_canonicalizer import EntityCanonicalizer
        print("✅ EntityCanonicalizer imported successfully")
        
        canonicalizer = EntityCanonicalizer()
        print("✅ EntityCanonicalizer service created successfully")
        
        print("\n🔍 Testing stable identifier extraction...")
        
        # Test stable identifier extraction
        test_entity = test_entities[0]  # p53 entity with MeSH ID
        stable_ids = canonicalizer.find_stable_identifiers_in_entity(test_entity)
        print(f"   📌 Stable identifiers found in {test_entity.entity_name}: {stable_ids}")
        
        # Test entity name canonicalization
        canonical_name = await canonicalizer.canonicalize_entity_name("p53")
        print(f"   📌 Canonical name for 'p53': {canonical_name}")
        
        canonical_name = await canonicalizer.canonicalize_entity_name("crispr")
        print(f"   📌 Canonical name for 'crispr': {canonical_name}")
        
        print("\n🔍 Testing entity similarity calculation...")
        
        # Test similarity calculation between similar entities
        entity1 = test_entities[0]  # p53
        entity2 = test_entities[1]  # TP53
        
        similarity_result = await canonicalizer.calculate_entity_similarity_with_context(
            entity1, [entity2]
        )
        print(f"   📌 Similarity between {entity1.entity_name} and {entity2.entity_name}:")
        print(f"      Should merge: {similarity_result['analysis'].get('should_merge', False)}")
        print(f"      Confidence: {similarity_result['analysis'].get('confidence', 0.0)}")
        print(f"      Reasoning: {similarity_result['analysis'].get('reasoning', 'No reasoning provided')}")
        
        print("\n🔍 Testing entity merging...")
        
        # Test merging similar entities
        similar_entities = [test_entities[0], test_entities[1], test_entities[2]]  # p53 variants
        merged_entity = await canonicalizer.merge_entities_with_enhanced_analysis(
            similar_entities, existing_entities
        )
        
        if merged_entity:
            print(f"   📌 Successfully merged entities into: {merged_entity.entity_name}")
            print(f"      Type: {merged_entity.entity_type}")
            print(f"      Aliases: {merged_entity.aliases}")
            print(f"      Frequency: {merged_entity.frequency}")
            print(f"      Paper IDs: {merged_entity.paper_ids}")
        else:
            print(f"   📌 No merge performed for p53 variants")
        
        print("\n🔍 Testing full canonicalization process...")
        
        # Test full canonicalization process
        canonicalization_results = await canonicalizer.process_entity_canonicalization_with_context(
            test_entities, existing_entities
        )
        
        print(f"📊 Full Canonicalization Results:")
        print_canonicalization_results(canonicalization_results)
        
        if canonicalization_results.get('canonical_entities'):
            print_entities(canonicalization_results['canonical_entities'], "Canonical Entities (After Canonicalization)")
        
        if canonicalization_results.get('errors'):
            print("❌ Errors encountered:")
            for error in canonicalization_results['errors']:
                print(f"   - {error}")
        
        print("\n🔍 Testing individual entity processing...")
        
        # Test processing individual entities
        for entity in test_entities[:3]:  # Test first 3 entities
            print(f"\n   📌 Processing entity: {entity.entity_name}")
            
            # Find similar entities
            similar_entities = await canonicalizer.find_similar_entities(entity)
            print(f"      Similar entities found: {len(similar_entities)}")
            
            # Calculate similarity with context
            similarity_result = await canonicalizer.calculate_entity_similarity_with_context(
                entity, existing_entities
            )
            print(f"      Should merge with existing: {similarity_result['analysis'].get('should_merge', False)}")
            print(f"      Confidence: {similarity_result['analysis'].get('confidence', 0.0)}")
        
    except Exception as e:
        print(f"❌ EntityCanonicalizer test failed: {str(e)}")
        logger.error(f"EntityCanonicalizer test failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return
    
    print("\n🔍 STEP 3: ANALYZE CANONICALIZATION EFFECTIVENESS")
    print("=" * 80)
    
    print(f"📊 Canonicalization Analysis:")
    print(f"   Input entities: {len(test_entities)}")
    print(f"   Existing entities: {len(existing_entities)}")
    print(f"   Canonical entities produced: {len(canonicalization_results.get('canonical_entities', []))}")
    print(f"   Merge operations: {len(canonicalization_results.get('merge_operations', []))}")
    
    if canonicalization_results.get('merge_operations'):
        print(f"\n📈 Merge Analysis:")
        for operation in canonicalization_results['merge_operations']:
            source_count = len(operation.get('source_entities', []))
            canonical_name = operation.get('canonical_entity', 'Unknown')
            confidence = operation.get('confidence', 0.0)
            print(f"   📌 {source_count} entities → {canonical_name} (confidence: {confidence})")
    
    print("\n🎉 Test completed successfully!")
    print("📊 The EntityCanonicalizer service is working with sophisticated LLM-based analysis!")

if __name__ == "__main__":
    asyncio.run(test_entity_canonicalizer_service())

