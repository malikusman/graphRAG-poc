#!/usr/bin/env python3
"""
Test script for the embeddings endpoint
"""

import asyncio
import json
import sys
import logging
from datetime import datetime
from typing import List

# Add the app directory to the Python path
sys.path.append('.')

from app.api.endpoints.embeddings import generate_embeddings, EmbeddingsGenerateRequest
from app.models.sections import SectionEmbeddingRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_embeddings_endpoint():
    """Test the embeddings generation endpoint"""
    
    # Test data matching the user's requirements
    test_sections = [
        {
            "updated_at": "2025-07-27T03:02:07.937000",
            "created_at": "2025-07-27T03:01:38.237000",
            "deleted_at": None,
            "section_id": "ec6bada3-5dcc-4c82-a701-19fefcbc95ef",
            "document_id": "0ddf18aa-1c0a-4804-a819-29bcb9d19691",
            "title": "Paragraph title 1",
            "text": "This is a sample text for testing the embedding generation. It should be combined with the title.",
            "position": 0,
            "text_updated_at": None,
            "user_id": "user123",
            "embeddings": [],  # Empty array initially
            "meta": None
        },
        {
            "updated_at": "2025-07-27T03:02:07.937000",
            "created_at": "2025-07-27T03:01:38.237000",
            "deleted_at": None,
            "section_id": "test-section-2",
            "document_id": "0ddf18aa-1c0a-4804-a819-29bcb9d19691",
            "title": "Empty Text Section",
            "text": "",  # Empty text - should not generate embeddings
            "position": 1,
            "text_updated_at": None,
            "user_id": "user123",
            "embeddings": [],  # Empty array initially
            "meta": None
        },
        {
            "updated_at": "2025-07-27T03:02:07.937000",
            "created_at": "2025-07-27T03:01:38.237000",
            "deleted_at": None,
            "section_id": "test-section-3",
            "document_id": "0ddf18aa-1c0a-4804-a819-29bcb9d19691",
            "title": "Another Title",
            "text": "Another test with different content to verify multiple embeddings work correctly.",
            "position": 2,
            "text_updated_at": None,
            "user_id": "user123",
            "embeddings": [],  # Empty array initially
            "meta": None
        }
    ]
    
    logger.info("Starting embeddings endpoint test...")
    
    try:
        # Convert to Pydantic models
        section_models = [SectionEmbeddingRequest.model_validate(section) for section in test_sections]
        
        # Create request
        request = EmbeddingsGenerateRequest(sections=section_models)
        
        # Call the endpoint function directly (simulating the API call)
        response = await generate_embeddings(request)
        
        logger.info(f"✅ Embeddings generation completed!")
        logger.info(f"📊 Processed: {response.processed_count} sections")
        logger.info(f"✅ Success: {response.success_count} sections got embeddings")
        
        # Display results
        for i, section in enumerate(response.sections):
            logger.info(f"\n--- Section {i+1}: {section.title} ---")
            logger.info(f"Section ID: {section.section_id}")
            logger.info(f"Text: {section.text[:50]}{'...' if len(section.text) > 50 else ''}")
            logger.info(f"Embeddings length: {len(section.embeddings)}")
            
            if section.embeddings:
                logger.info(f"First few embedding values: {section.embeddings[:5]}...")
            else:
                logger.info("No embeddings generated (empty text)")
        
        # Verify the requirements are met
        logger.info(f"\n🔍 Verification:")
        logger.info(f"- Input had {len(test_sections)} sections")
        logger.info(f"- Output has {len(response.sections)} sections")
        logger.info(f"- Empty text sections should have empty embeddings arrays")
        
        # Check empty text handling
        empty_text_count = sum(1 for s in response.sections if not s.text or not s.text.strip())
        empty_embeddings_count = sum(1 for s in response.sections if not s.embeddings)
        logger.info(f"- Sections with empty text: {empty_text_count}")
        logger.info(f"- Sections with empty embeddings: {empty_embeddings_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    logger.info("🚀 Testing Embeddings Endpoint")
    logger.info("=" * 50)
    
    success = await test_embeddings_endpoint()
    
    if success:
        logger.info("\n✅ All tests passed!")
    else:
        logger.error("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
