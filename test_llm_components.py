#!/usr/bin/env python3
"""
LLM Components Test
Tests the core LLM functionality for entity and relationship extraction
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
        logging.FileHandler('llm_components_test.log')
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

def print_llm_response(title: str, response: any):
    """Print LLM response in detail"""
    print(f"\n🤖 {title}:")
    if isinstance(response, dict):
        for key, value in response.items():
            if isinstance(value, list):
                print(f"   {key}: [{len(value)} items]")
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        print(f"     {i+1}. {item}")
                    else:
                        print(f"     {i+1}. {item}")
            else:
                print(f"   {key}: {value}")
    else:
        print(f"   {response}")

async def test_llm_components():
    """Test the LLM components with detailed logging"""
    print("🚀 Starting LLM Components Test")
    print("="*80)
    
    # Create test document data
    test_sections = [
        {
            "_id": "section_001",
            "title": "Introduction",
            "text": "The tumor suppressor protein p53 plays a crucial role in maintaining genomic stability and preventing cancer development. It interacts with MDM2 (murine double minute 2), which targets p53 for proteasomal degradation. Mutations in the TP53 gene are associated with various cancers including breast cancer, lung cancer, and colorectal cancer. The p53-MDM2 interaction is a critical regulatory mechanism in cell cycle control."
        },
        {
            "_id": "section_002", 
            "title": "Methods",
            "text": "We used CRISPR-Cas9 gene editing technology to modify the TP53 gene in human cancer cell lines. The cells were cultured in DMEM (Dulbecco's Modified Eagle Medium) supplemented with 10% fetal bovine serum at 37°C in a 5% CO2 atmosphere. Western blot analysis was performed to detect p53 protein expression levels. Immunoprecipitation assays were used to study the p53-MDM2 protein interaction."
        }
    ]
    
    try:
        # Import core components
        from app.core.config import settings
        from app.configs.schemas import load_prompt
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser
        
        print("✅ Core components imported successfully")
        
        # Initialize LLM
        print("\n🔧 Initializing LLM...")
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        print(f"✅ LLM initialized: {settings.OPENAI_MODEL}")
        
        # Load prompts
        print("\n📋 Loading prompts...")
        entity_prompt_config = load_prompt("entity_extraction", "map")
        relationship_prompt_config = load_prompt("relationship_extraction", "map")
        print("✅ Prompts loaded successfully")
        
        # Create prompt templates
        entity_prompt = ChatPromptTemplate.from_template(
            entity_prompt_config["user_prompt"]
        )
        relationship_prompt = ChatPromptTemplate.from_template(
            relationship_prompt_config["user_prompt"]
        )
        print("✅ Prompt templates created")
        
        # Create output parsers
        entity_parser = JsonOutputParser()
        relationship_parser = JsonOutputParser()
        print("✅ Output parsers created")
        
        # ============================================================================
        # STEP 1: ENTITY EXTRACTION - REAL LLM CALLS
        # ============================================================================
        print_step_header(1, "ENTITY EXTRACTION", "Extract entities from each section using REAL LLM calls")
        
        print("\n📄 Input Sections:")
        for i, section in enumerate(test_sections):
            print(f"   Section {i+1}: {section['title']}")
            print(f"   Text: {section['text'][:150]}...")
        
        # Test entity extraction for each section with real LLM calls
        all_entities = []
        for i, section in enumerate(test_sections):
            print(f"\n🤖 Processing Section {i+1} with REAL LLM...")
            
            # Create entity extraction chain
            entity_chain = entity_prompt | llm | entity_parser
            
            # Extract entities from section
            print(f"📤 Sending to LLM for entity extraction...")
            print(f"   Section text length: {len(section['text'])} characters")
            
            result = await entity_chain.ainvoke({
                "section_text": section["text"],
                "section_title": section.get("title", "")
            })
            
            print_llm_response(f"LLM Response for Section {i+1}", result)
            
            # Process extracted entities
            if "entities" in result:
                entities = result["entities"]
                print(f"\n🏷️ Extracted {len(entities)} entities from section {i+1}")
                
                for j, entity in enumerate(entities):
                    entity["section_id"] = str(section["_id"])
                    entity["provenance"] = entity.get("provenance", section["text"][:200])
                    all_entities.append(entity)
                    
                    print(f"   Entity {j+1}: {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
                    print(f"     Category: {entity.get('entity_category', 'N/A')}")
                    print(f"     Aliases: {entity.get('aliases', [])}")
                    print(f"     Description: {entity.get('description', 'N/A')[:100]}...")
            else:
                print(f"❌ No entities found in LLM response for section {i+1}")
                print(f"   Full response: {result}")
        
        print_data("All Extracted Entities", all_entities)
        print(f"\n✅ STEP 1 Complete: {len(all_entities)} entities extracted from {len(test_sections)} sections")
        
        # ============================================================================
        # STEP 2: RELATIONSHIP EXTRACTION - REAL LLM CALLS
        # ============================================================================
        print_step_header(2, "RELATIONSHIP EXTRACTION", "Extract relationships between entities using REAL LLM calls")
        
        all_relationships = []
        for i, section in enumerate(test_sections):
            print(f"\n🤖 Processing Section {i+1} for relationships with REAL LLM...")
            
            # Get entities from this section
            section_entities = [e for e in all_entities if e["section_id"] == str(section["_id"])]
            print(f"🏷️ Found {len(section_entities)} entities in section {i+1}")
            
            if len(section_entities) < 2:
                print(f"⚠️ Skipping section {i+1}: Need at least 2 entities for relationships")
                continue
            
            # Create entities list for prompt
            entities_list = [f"- {e['entity_name']} ({e['entity_type']})" for e in section_entities]
            entities_text = "\n".join(entities_list)
            print(f"📋 Entities list for prompt: {entities_text}")
            
            # Create relationship extraction chain
            relationship_chain = relationship_prompt | llm | relationship_parser
            
            # Extract relationships from section
            print(f"📤 Sending to LLM for relationship extraction...")
            
            result = await relationship_chain.ainvoke({
                "section_text": section["text"],
                "section_title": section.get("title", ""),
                "entities_list": entities_text
            })
            
            print_llm_response(f"LLM Response for Section {i+1}", result)
            
            # Process extracted relationships
            if "relationships" in result:
                relationships = result["relationships"]
                print(f"\n🔗 Extracted {len(relationships)} relationships from section {i+1}")
                
                for j, rel in enumerate(relationships):
                    rel["section_id"] = str(section["_id"])
                    rel["provenance"] = rel.get("provenance", section["text"][:200])
                    all_relationships.append(rel)
                    
                    print(f"   Relationship {j+1}: {rel.get('source_entity', 'N/A')} -> {rel.get('target_entity', 'N/A')}")
                    print(f"     Type: {rel.get('relationship_type', 'N/A')}")
                    print(f"     Strength: {rel.get('relationship_strength', 'N/A')}")
                    print(f"     Description: {rel.get('description', 'N/A')[:100]}...")
            else:
                print(f"❌ No relationships found in LLM response for section {i+1}")
                print(f"   Full response: {result}")
        
        print_data("All Extracted Relationships", all_relationships)
        print(f"\n✅ STEP 2 Complete: {len(all_relationships)} relationships extracted")
        
        # ============================================================================
        # STEP 3: DATA PROCESSING
        # ============================================================================
        print_step_header(3, "DATA PROCESSING", "Process and analyze the extracted data")
        
        # Analyze entities
        entity_types = {}
        entity_categories = {}
        for entity in all_entities:
            entity_type = entity.get('entity_type', 'Unknown')
            entity_category = entity.get('entity_category', 'Unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            entity_categories[entity_category] = entity_categories.get(entity_category, 0) + 1
        
        print(f"\n📊 Entity Analysis:")
        print(f"   Total entities: {len(all_entities)}")
        print(f"   Entity types: {entity_types}")
        print(f"   Entity categories: {entity_categories}")
        
        # Analyze relationships
        relationship_types = {}
        strength_distribution = {}
        for rel in all_relationships:
            rel_type = rel.get('relationship_type', 'Unknown')
            strength = rel.get('relationship_strength', 0)
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
            
            # Group strengths
            if strength < 0.3:
                strength_distribution['Low (<0.3)'] = strength_distribution.get('Low (<0.3)', 0) + 1
            elif strength < 0.7:
                strength_distribution['Medium (0.3-0.7)'] = strength_distribution.get('Medium (0.3-0.7)', 0) + 1
            else:
                strength_distribution['High (>0.7)'] = strength_distribution.get('High (>0.7)', 0) + 1
        
        print(f"\n📊 Relationship Analysis:")
        print(f"   Total relationships: {len(all_relationships)}")
        print(f"   Relationship types: {relationship_types}")
        print(f"   Strength distribution: {strength_distribution}")
        
        # ============================================================================
        # FINAL SUMMARY
        # ============================================================================
        print(f"\n{'='*80}")
        print("🎯 LLM COMPONENTS TEST SUMMARY")
        print(f"{'='*80}")
        
        print(f"📝 Sections processed: {len(test_sections)}")
        print(f"🏷️ Entities extracted: {len(all_entities)}")
        print(f"🔗 Relationships extracted: {len(all_relationships)}")
        
        print(f"\n🏷️ Entity Breakdown:")
        for entity_type, count in entity_types.items():
            print(f"   {entity_type}: {count}")
        
        print(f"\n🔗 Relationship Breakdown:")
        for rel_type, count in relationship_types.items():
            print(f"   {rel_type}: {count}")
        
        print(f"\n🎉 LLM components test completed successfully!")
        print(f"📊 The LLM successfully extracted {len(all_entities)} entities and {len(all_relationships)} relationships")
        print(f"   from {len(test_sections)} sections of scientific text.")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM components test failed: {str(e)}")
        logger.exception("LLM components test failed")
        return False

async def main():
    """Run the LLM components test"""
    success = await test_llm_components()
    
    if success:
        print("\n🎉 LLM components test completed successfully!")
        print("📊 Check the logs for detailed information about LLM responses and data transformations.")
    else:
        print("\n❌ LLM components test failed!")
        print("📊 Check the logs for error details.")

if __name__ == "__main__":
    asyncio.run(main())

