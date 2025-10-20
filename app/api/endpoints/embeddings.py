"""
API endpoints for embedding generation
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.sections import SectionEmbeddingRequest
from app.services.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])

# Initialize embeddings service
embeddings_service = EmbeddingsService()


class EmbeddingsGenerateRequest(BaseModel):
    """Request model for batch embedding generation"""
    sections: List[SectionEmbeddingRequest] = Field(..., description="List of sections to generate embeddings for")


class EmbeddingsGenerateResponse(BaseModel):
    """Response model for batch embedding generation"""
    sections: List[SectionEmbeddingRequest] = Field(..., description="List of sections with generated embeddings")
    processed_count: int = Field(..., description="Number of sections processed")
    success_count: int = Field(..., description="Number of sections that successfully got embeddings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sections": [
                    {
                        "updated_at": "2025-07-27T03:02:07.937000",
                        "created_at": "2025-07-27T03:01:38.237000",
                        "deleted_at": None,
                        "section_id": "ec6bada3-5dcc-4c82-a701-19fefcbc95ef",
                        "document_id": "0ddf18aa-1c0a-4804-a819-29bcb9d19691",
                        "title": "Paragraph title 1",
                        "text": "Sample text content",
                        "position": 0,
                        "text_updated_at": None,
                        "user_id": "user123",
                        "embeddings": [0.123, -0.456, 0.789, ...],
                        "meta": None
                    }
                ],
                "processed_count": 1,
                "success_count": 1
            }
        }


@router.post("/generate", response_model=EmbeddingsGenerateResponse)
async def generate_embeddings(request: EmbeddingsGenerateRequest):
    """
    Generate embeddings for a list of sections
    
    This endpoint receives a list of sections with potentially empty embeddings arrays
    and returns the same list with generated embeddings for sections that have text content.
    
    **Key Features:**
    - Skips embedding generation for sections with empty text
    - Combines title and text for better semantic representation
    - Returns empty embeddings array for sections with no text
    - Processes sections in batch for efficiency
    
    **Request Format:**
    Each section should include:
    - `section_id`: Unique identifier for the section
    - `title`: Section title (used in combination with text for embedding)
    - `text`: Section content (must not be empty to generate embedding)
    - `embeddings`: Empty array initially, will be populated in response
    
    **Response:**
    Returns the same section list with populated `embeddings` arrays where applicable.
    """
    try:
        logger.info(f"Starting embedding generation for {len(request.sections)} sections")
        
        # Convert Pydantic models to dictionaries for processing
        sections_data = [section.model_dump() for section in request.sections]
        
        # Generate embeddings using the batch service
        processed_sections = embeddings_service.generate_section_embeddings_batch(sections_data)
        
        # Count successful embeddings (non-empty arrays)
        success_count = sum(
            1 for section in processed_sections 
            if section.get('embeddings') and len(section.get('embeddings', [])) > 0
        )
        
        # Convert back to Pydantic models for response
        response_sections = [
            SectionEmbeddingRequest.model_validate(section) 
            for section in processed_sections
        ]
        
        logger.info(f"Completed embedding generation: {success_count}/{len(processed_sections)} sections got embeddings")
        
        return EmbeddingsGenerateResponse(
            sections=response_sections,
            processed_count=len(processed_sections),
            success_count=success_count
        )
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for embeddings service"""
    try:
        # Test embedding service connectivity
        model_name = embeddings_service.get_model_name()
        dimensions = embeddings_service.get_embedding_dimensions()
        
        return {
            "status": "healthy",
            "service": "embeddings",
            "model": model_name,
            "dimensions": dimensions,
            "message": "Embeddings service is running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
