"""
Embedding Provider Abstraction Layer

Provides a unified interface for different embedding providers (OpenAI, Bedrock)
to allow easy switching between providers via configuration.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values or None if failed
        """
        pass
    
    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed ones)
        """
        pass
    
    @abstractmethod
    def get_embedding_dimensions(self) -> int:
        """Get the number of dimensions for embeddings"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the embedding model name"""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI embedding provider")
        
        # Set max tokens and dimensions based on model
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
        """Generate OpenAI embedding"""
        try:
            # Truncate text if too long
            if len(text) > self.max_tokens * 4:  # Rough character to token ratio
                text = text[:self.max_tokens * 4]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated OpenAI embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate OpenAI embeddings for multiple texts"""
        embeddings = []
        
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def get_embedding_dimensions(self) -> int:
        """Get OpenAI embedding dimensions"""
        return self.dimensions
    
    def get_model_name(self) -> str:
        """Get OpenAI model name"""
        return self.model


class BedrockEmbeddingProvider(BaseEmbeddingProvider):
    """Amazon Bedrock embedding provider using BedrockEmbeddings"""
    
    def __init__(self):
        try:
            from app.core.bedrock_wrapper import BedrockEmbeddings
            self.BedrockEmbeddings = BedrockEmbeddings
        except ImportError as e:
            raise ImportError(
                f"Failed to import Bedrock embeddings wrapper. "
                f"Make sure boto3 is installed: poetry add boto3. "
                f"Error: {str(e)}"
            )
        
        self.model_id = settings.BEDROCK_EMBEDDING_MODEL_ID
        self.region = settings.BEDROCK_REGION
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        
        if not self.region:
            raise ValueError("BEDROCK_REGION is required when using Bedrock embedding provider")
        if not self.model_id:
            raise ValueError("BEDROCK_EMBEDDING_MODEL_ID is required when using Bedrock embedding provider")
        
        # Initialize Bedrock client
        self.credentials = {}
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.credentials = {
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
            }
            logger.info("Using AWS access keys for Bedrock embeddings")
        else:
            logger.info("Using IAM role or default AWS credential chain for Bedrock embeddings")
        
        # Set dimensions based on model
        # Titan v2: 1024, Titan v1: 1536
        if "titan-embed-text-v2" in self.model_id:
            self.dimensions = 1024
        elif "titan-embed-text-v1" in self.model_id:
            self.dimensions = 1536
        else:
            # Default to v2 dimensions
            self.dimensions = 1024
            logger.warning(f"Unknown embedding model, defaulting to {self.dimensions} dimensions")
        
        # Create embeddings instance
        try:
            bedrock_kwargs = {
                "model_id": self.model_id,
                "region_name": self.region,
                **self.credentials
            }
            self.embeddings_client = self.BedrockEmbeddings(**bedrock_kwargs)
            logger.info(f"Initialized Bedrock embeddings with model {self.model_id}, {self.dimensions} dimensions")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock embeddings: {str(e)}")
            raise ValueError(
                f"Failed to initialize Bedrock embedding provider. "
                f"Make sure AWS credentials are configured and model access is enabled. "
                f"Error: {str(e)}"
            )
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate Bedrock embedding"""
        try:
            # BedrockEmbeddings expects a list
            embeddings = self.embeddings_client.embed_documents([text])
            
            if embeddings and len(embeddings) > 0:
                embedding = embeddings[0]
                logger.debug(f"Generated Bedrock embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.error("Bedrock returned empty embedding")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Bedrock embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate Bedrock embeddings for multiple texts"""
        try:
            # BedrockEmbeddings can handle batch
            embeddings = self.embeddings_client.embed_documents(texts)
            
            # Convert to list of Optional[List[float]]
            result = []
            for embedding in embeddings:
                if embedding:
                    result.append(embedding)
                else:
                    result.append(None)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating Bedrock embeddings batch: {str(e)}")
            # Return None for all on batch failure
            return [None] * len(texts)
    
    def get_embedding_dimensions(self) -> int:
        """Get Bedrock embedding dimensions"""
        return self.dimensions
    
    def get_model_name(self) -> str:
        """Get Bedrock model ID"""
        return self.model_id


def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    Factory function to get the appropriate embedding provider based on configuration
    
    Returns:
        BaseEmbeddingProvider instance
        
    Raises:
        ValueError: If provider is not supported or not configured correctly
    """
    provider_name = settings.EMBEDDING_PROVIDER.lower()
    
    if provider_name == "openai":
        logger.info("Initializing OpenAI embedding provider")
        return OpenAIEmbeddingProvider()
    elif provider_name == "bedrock":
        logger.info("Initializing Bedrock embedding provider")
        return BedrockEmbeddingProvider()
    else:
        raise ValueError(
            f"Unsupported embedding provider: {provider_name}. "
            f"Supported providers: 'openai', 'bedrock'"
        )

