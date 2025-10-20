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
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
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
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed ones)
        """
        embeddings = []
        
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def generate_section_embedding(self, section_text: str, section_title: str = "") -> Optional[List[float]]:
        """
        Generate embedding for a section with title context
        
        Args:
            section_text: Main section text
            section_title: Section title for context
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            # Combine title and text for better context using the format specified in the plan
            if section_title and section_text:
                combined_text = f"Title: {section_title}. Text: {section_text}"
            elif section_title:
                combined_text = f"Title: {section_title}."
            elif section_text:
                combined_text = section_text
            else:
                # Both are empty, return None
                logger.warning("Both title and text are empty, skipping embedding generation")
                return None
            
            return self.generate_embedding(combined_text)
            
        except Exception as e:
            logger.error(f"Error generating section embedding: {str(e)}")
            return None
    
    def get_embedding_dimensions(self) -> int:
        """Get the number of dimensions for embeddings"""
        return self.dimensions
    
    def get_model_name(self) -> str:
        """Get the embedding model name"""
        return self.model
    
    def generate_section_embeddings_batch(self, sections: List[dict]) -> List[dict]:
        """
        Generate embeddings for multiple sections with title and text combination
        
        Args:
            sections: List of section dictionaries with 'title' and 'text' keys
            
        Returns:
            List of section dictionaries with populated 'embeddings' field
        """
        processed_sections = []
        
        for section in sections:
            # Create a copy to avoid modifying the original
            processed_section = section.copy()
            
            # Check if text is empty or None
            text = section.get('text', '')
            title = section.get('title', '')
            
            if not text or not text.strip():
                # Keep empty embeddings array for empty text as specified in requirements
                processed_section['embeddings'] = []
                logger.debug(f"Skipping embedding generation for section {section.get('section_id', 'unknown')} - empty text")
            else:
                # Generate embedding with title and text combination
                embedding = self.generate_section_embedding(text, title)
                if embedding:
                    processed_section['embeddings'] = embedding
                else:
                    processed_section['embeddings'] = []
                    logger.warning(f"Failed to generate embedding for section {section.get('section_id', 'unknown')}")
            
            processed_sections.append(processed_section)
        
        return processed_sections
