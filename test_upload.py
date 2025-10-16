#!/usr/bin/env python3
"""
Test script to upload and process a document through our GraphRAG system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.document_service import DocumentService
from app.services.file_parser import FileParser
from app.services.metadata_extractor import MetadataExtractor
from app.services.section_extractor import SectionExtractor
from app.pipelines.graphrag_pipeline import GraphRAGPipeline

class MockUploadFile:
    """Mock UploadFile for testing"""
    def __init__(self, file_path: str):
        self.filename = os.path.basename(file_path)
        self.file_path = file_path
    
    async def read(self):
        with open(self.file_path, 'rb') as f:
            return f.read()

async def test_file_parsing():
    """Test file parsing services"""
    print("🧪 Testing File Parsing Services...")
    
    # Test file parsing
    mock_file = MockUploadFile("test_paper.txt")
    parsed_content = await FileParser.parse_file(mock_file)
    print(f"✅ File parsed: {parsed_content['file_type']}, {len(parsed_content['content'])} characters")
    
    # Test metadata extraction
    metadata = MetadataExtractor.extract_metadata(parsed_content["content"], mock_file.filename)
    print(f"✅ Metadata extracted: {metadata}")
    
    # Test section extraction
    sections = SectionExtractor.extract_sections(
        parsed_content["content"], 
        "test_doc_123", 
        metadata["year"]
    )
    
    # Add mock MongoDB _id fields for testing
    for i, section in enumerate(sections):
        section["_id"] = f"section_{i+1}"
    
    print(f"✅ Sections extracted: {len(sections)} sections")
    for i, section in enumerate(sections):
        print(f"   {i+1}. {section['title']} ({len(section['text'])} chars)")
    
    return sections

async def test_graphrag_pipeline(sections):
    """Test GraphRAG pipeline"""
    print("\n🧪 Testing GraphRAG Pipeline...")
    
    # Initialize pipeline
    pipeline = GraphRAGPipeline()
    
    # Process document
    result = await pipeline.process_document("test_doc_123", sections)
    
    print(f"✅ GraphRAG processing result: {result}")
    
    # If successful, let's also get the detailed results
    if result.get("success"):
        print(f"\n📊 Detailed Results:")
        print(f"   - Raw entities extracted: {result.get('entities_extracted', 0)}")
        print(f"   - Raw relationships extracted: {result.get('relationships_extracted', 0)}")
        print(f"   - Final unique entities: {result.get('final_entities', 0)}")
        print(f"   - Final unique relationships: {result.get('final_relationships', 0)}")
        
        # Let's also test individual components to see the actual data
        await test_individual_components(sections)
    
    return result

async def test_individual_components(sections):
    """Test individual components to see actual extracted data"""
    print(f"\n🔍 Testing Individual Components...")
    
    from app.pipelines.graphrag_pipeline import GraphRAGPipeline
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from app.configs.schemas import load_prompt
    from app.core.config import settings
    
    # Initialize LLM and prompts
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY
    )
    
    entity_prompt_config = load_prompt("entity_extraction", "map")
    entity_prompt = ChatPromptTemplate.from_template(entity_prompt_config["user_prompt"])
    entity_parser = JsonOutputParser()
    
    # Test entity extraction on first section (abstract)
    if sections:
        abstract_section = sections[0]  # Abstract
        print(f"\n📝 Testing Entity Extraction on Abstract:")
        print(f"   Section: {abstract_section['title']}")
        print(f"   Text preview: {abstract_section['text'][:200]}...")
        
        try:
            entity_chain = entity_prompt | llm | entity_parser
            entity_result = await entity_chain.ainvoke({
                "section_text": abstract_section["text"],
                "section_title": abstract_section["title"]
            })
            
            print(f"\n🎯 Entities Extracted from Abstract:")
            if "entities" in entity_result:
                for i, entity in enumerate(entity_result["entities"], 1):
                    print(f"   {i}. {entity.get('entity_name', 'N/A')} ({entity.get('entity_type', 'N/A')})")
                    print(f"      Category: {entity.get('entity_category', 'N/A')}")
                    print(f"      Aliases: {entity.get('aliases', [])}")
                    print(f"      Description: {entity.get('description', 'N/A')[:100]}...")
                    print()
            else:
                print("   No entities found in result")
                print(f"   Raw result: {entity_result}")
                
        except Exception as e:
            print(f"   ❌ Error extracting entities: {str(e)}")
        
        # Test relationship extraction on methods section (more likely to have relationships)
        methods_section = None
        for section in sections:
            if section['title'].lower() in ['methods', 'methodology']:
                methods_section = section
                break
        
        if methods_section:
            print(f"\n🔗 Testing Relationship Extraction on Methods:")
            print(f"   Section: {methods_section['title']}")
            print(f"   Text preview: {methods_section['text'][:200]}...")
            
            # First extract entities from this section
            try:
                entity_result_methods = await entity_chain.ainvoke({
                    "section_text": methods_section["text"],
                    "section_title": methods_section["title"]
                })
                
                if "entities" in entity_result_methods and len(entity_result_methods["entities"]) >= 2:
                    # Create entities list for relationship prompt
                    entities_list = [f"- {e['entity_name']} ({e['entity_type']})" for e in entity_result_methods["entities"]]
                    entities_text = "\n".join(entities_list)
                    
                    # Test relationship extraction
                    relationship_prompt_config = load_prompt("relationship_extraction", "map")
                    relationship_prompt = ChatPromptTemplate.from_template(relationship_prompt_config["user_prompt"])
                    relationship_parser = JsonOutputParser()
                    
                    relationship_chain = relationship_prompt | llm | relationship_parser
                    relationship_result = await relationship_chain.ainvoke({
                        "section_text": methods_section["text"],
                        "section_title": methods_section["title"],
                        "entities_list": entities_text
                    })
                    
                    print(f"\n🎯 Relationships Extracted from Methods:")
                    if "relationships" in relationship_result:
                        for i, rel in enumerate(relationship_result["relationships"], 1):
                            print(f"   {i}. {rel.get('source_entity', 'N/A')} → {rel.get('relationship_type', 'N/A')} → {rel.get('target_entity', 'N/A')}")
                            print(f"      Strength: {rel.get('relationship_strength', 'N/A')}")
                            print(f"      Description: {rel.get('description', 'N/A')[:100]}...")
                            print()
                    else:
                        print("   No relationships found in result")
                        print(f"   Raw result: {relationship_result}")
                        
                else:
                    print(f"   Not enough entities found for relationship extraction: {len(entity_result_methods.get('entities', []))}")
                    
            except Exception as e:
                print(f"   ❌ Error extracting relationships: {str(e)}")
        else:
            print("   No methods section found for relationship testing")

async def main():
    """Main test function"""
    print("🚀 Starting GraphRAG System Test\n")
    
    try:
        # Test file parsing
        sections = await test_file_parsing()
        
        # Test GraphRAG pipeline
        result = await test_graphrag_pipeline(sections)
        
        print(f"\n🎉 Test completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Sections processed: {len(sections)}")
        print(f"   - Entities extracted: {result.get('entities_extracted', 0)}")
        print(f"   - Relationships extracted: {result.get('relationships_extracted', 0)}")
        print(f"   - Final entities: {result.get('final_entities', 0)}")
        print(f"   - Final relationships: {result.get('final_relationships', 0)}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
