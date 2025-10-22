"""
Test entity and relationship extraction prompts using LangSmith
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from langsmith import Client
from app.pipelines.graphrag_pipeline import GraphRAGPipeline
from app.core.config import settings

async def test_entity_extraction_prompts():
    """Test different entity extraction prompt variations"""
    client = Client()
    
    # Test document
    test_sections = [
        {
            "_id": "test_1",
            "title": "CRISPR-Cas9 Gene Editing",
            "text": "CRISPR-Cas9 is a revolutionary gene-editing technology that allows precise modifications to DNA. Developed by Jennifer Doudna and Emmanuelle Charpentier, it has transformed genetic research."
        }
    ]
    
    # Run pipeline with current prompts
    pipeline = GraphRAGPipeline()
    result = await pipeline.process_document("test_doc", test_sections)
    
    print(f"Entities extracted: {len(result['final_entities'])}")
    for entity in result['final_entities']:
        print(f"  - {entity['entity_name']} ({entity['entity_type']})")
    
    # View results in LangSmith dashboard at:
    # https://smith.langchain.com/
    print(f"\nView trace at: https://smith.langchain.com/public/{settings.LANGCHAIN_PROJECT}")

if __name__ == "__main__":
    asyncio.run(test_entity_extraction_prompts())
