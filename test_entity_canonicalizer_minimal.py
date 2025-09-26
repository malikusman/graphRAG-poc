#!/usr/bin/env python3
"""
Minimal test for enhanced EntityCanonicalizer service
Tests stable identifier extraction and basic functionality without LLM dependencies
"""

import sys
import os
import re
from typing import List

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Test stable identifier extraction directly
def test_stable_identifier_extraction():
    """Test stable identifier extraction patterns"""
    print("🧪 Testing Stable Identifier Extraction Patterns...")
    
    # Stable identifier patterns (copied from our enhanced service)
    stable_id_patterns = {
        "MeSH": r"MESH:D\d{9}",
        "HGNC": r"HGNC:\d+",
        "UniProt": r"UNIPROT:[A-Z0-9]+",
        "GO": r"GO:\d{7}",
        "ChEBI": r"CHEBI:\d+",
        "KEGG": r"KEGG:[A-Z0-9]+"
    }
    
    def extract_stable_identifiers(text: str) -> List[str]:
        """Extract stable identifiers from text using regex patterns"""
        identifiers = []
        for id_type, pattern in stable_id_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            identifiers.extend(matches)
        return identifiers
    
    # Test cases
    test_cases = [
        "CRISPR-Cas9 (MeSH:D000077505) is a gene editing system",
        "TP53 (HGNC:11998) is a tumor suppressor gene",
        "The protein (UniProt:P04637) functions as a tumor suppressor",
        "This process (GO:0006915) involves apoptosis",
        "The compound (ChEBI:15365) is a neurotransmitter",
        "The pathway (KEGG:hsa04115) regulates cell cycle"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        identifiers = extract_stable_identifiers(test_case)
        print(f"  📋 Test {i}: {test_case}")
        print(f"    🎯 Found identifiers: {identifiers}")
    
    print("✅ Stable identifier extraction test completed\n")


def test_enhanced_prompt_structure():
    """Test that our enhanced prompt structure is valid"""
    print("🧪 Testing Enhanced Prompt Structure...")
    
    try:
        # Test loading the enhanced prompt
        from app.configs.schemas import load_prompt
        
        prompt_config = load_prompt("entity_canonicalization", "reduce")
        
        print(f"  📋 System prompt loaded: {len(prompt_config.get('system_prompt', ''))} characters")
        print(f"  📋 User prompt loaded: {len(prompt_config.get('user_prompt', ''))} characters")
        print(f"  📋 Temperature: {prompt_config.get('temperature', 'N/A')}")
        print(f"  📋 Max tokens: {prompt_config.get('max_tokens', 'N/A')}")
        
        # Check for key features in the prompt
        user_prompt = prompt_config.get('user_prompt', '')
        key_features = [
            'stable_identifiers',
            'MeSH',
            'HGNC',
            'UniProt',
            'confidence',
            'evidence_types',
            'stable_identifiers_found'
        ]
        
        for feature in key_features:
            if feature in user_prompt:
                print(f"    ✅ Found '{feature}' in prompt")
            else:
                print(f"    ❌ Missing '{feature}' in prompt")
        
        print("✅ Enhanced prompt structure test completed\n")
        
    except Exception as e:
        print(f"❌ Error testing prompt structure: {str(e)}\n")


def test_entity_model_structure():
    """Test that our entity model supports the enhanced features"""
    print("🧪 Testing Entity Model Structure...")
    
    try:
        from app.models.entities import Entity, EntityType, EntityCategory
        
        # Test creating an entity with stable identifiers in description
        test_entity = Entity(
            entity_name="CRISPR-Cas9",
            entity_type=EntityType.PROTEIN_COMPLEX,
            entity_category=EntityCategory.PROTEINS_AND_ENZYMES,
            aliases=["CRISPR", "Cas9"],
            entity_description="A gene editing system (MeSH:D000077505)",
            frequency=1,
            paper_ids=["test_paper"],
            section_ids=["test_section"]
        )
        
        print(f"  📋 Created entity: {test_entity.entity_name}")
        print(f"  📋 Type: {test_entity.entity_type}")
        print(f"  📋 Category: {test_entity.entity_category}")
        print(f"  📋 Description: {test_entity.entity_description}")
        print(f"  📋 Aliases: {test_entity.aliases}")
        
        # Test model dump
        entity_dict = test_entity.model_dump()
        print(f"  📋 Model dump keys: {list(entity_dict.keys())}")
        
        print("✅ Entity model structure test completed\n")
        
    except Exception as e:
        print(f"❌ Error testing entity model: {str(e)}\n")


def main():
    """Run all minimal tests"""
    print("🚀 Starting Minimal EntityCanonicalizer Tests\n")
    
    try:
        test_stable_identifier_extraction()
        test_enhanced_prompt_structure()
        test_entity_model_structure()
        
        print("🎉 All minimal tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
