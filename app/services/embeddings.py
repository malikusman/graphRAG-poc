"""
OpenAI embeddings service for generating vector embeddings
"""

import logging
from typing import List, Optional
import openai
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating embeddings using OpenAI"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        # Set max tokens based on model
        if "text-embedding-3-small" in self.model:
            self.max_tokens = 8191
            self.dimensions = 1536
        elif "text-embedding-3-large" in self.model:
            self.max_tokens = 8191
            self.dimensions = 3072
        elif "text-embedding-ada-002" in self.model:
            self.max_tokens = 8191
            self.dimensions = 1536
        else:
            # Default fallback
            self.max_tokens = 8191
            self.dimensions = 1536
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values or None if failed
        """
        try:
            # Truncate text if too long
            if len(text) > self.max_tokens * 4:  # Rough character to token ratio
                text = text[:self.max_tokens * 4]
            
            response = await self.client.embeddings.acreate(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed ones)
        """
        embeddings = []
        
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    async def generate_section_embedding(self, section_text: str, section_title: str = "") -> Optional[List[float]]:
        """
        Generate embedding for a section with title context
        
        Args:
            section_text: Main section text
            section_title: Section title for context
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            # Combine title and text for better context
            if section_title:
                combined_text = f"{section_title}: {section_text}"
            else:
                combined_text = section_text
            
            return await self.generate_embedding(combined_text)
            
        except Exception as e:
            logger.error(f"Error generating section embedding: {str(e)}")
            return None
    
    def get_embedding_dimensions(self) -> int:
        """Get the number of dimensions for embeddings"""
        return self.dimensions
    
    def get_model_name(self) -> str:
        """Get the embedding model name"""
        return self.model
