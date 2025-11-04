"""
Embedding Provider Abstraction Layer

Provides a unified interface for different embedding providers (OpenAI, Bedrock, Vertex AI)
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
    """Amazon Bedrock embedding provider using official langchain-aws package"""
    
    def __init__(self):
        try:
            from langchain_aws import BedrockEmbeddings
            self.BedrockEmbeddings = BedrockEmbeddings
        except ImportError as e:
            raise ImportError(
                f"Failed to import BedrockEmbeddings from langchain-aws. "
                f"Make sure langchain-aws is installed: poetry add langchain-aws. "
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
        
        # Initialize Bedrock embeddings client
        if self.aws_access_key_id and self.aws_secret_access_key:
            logger.info("Using AWS access keys for Bedrock embeddings")
        else:
            logger.info("Using IAM role or default AWS credential chain for Bedrock embeddings")
        
        # Create embeddings instance
        try:
            from pydantic import SecretStr
            
            bedrock_kwargs = {
                "model_id": self.model_id,
                "region_name": self.region,
            }
            
            # Add credentials if provided (langchain-aws uses SecretStr)
            if self.aws_access_key_id and self.aws_secret_access_key:
                bedrock_kwargs["aws_access_key_id"] = SecretStr(self.aws_access_key_id)
                bedrock_kwargs["aws_secret_access_key"] = SecretStr(self.aws_secret_access_key)
            # Note: If credentials not provided, langchain-aws uses boto3 credential chain
            # (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars, IAM roles, or ~/.aws/credentials)
            
            self.embeddings_client = self.BedrockEmbeddings(**bedrock_kwargs)
            logger.info(f"Initialized Bedrock embeddings with model {self.model_id}, {self.dimensions} dimensions")
        except ImportError as e:
            logger.error(f"Failed to import Bedrock dependencies: {str(e)}")
            raise ImportError(
                f"Failed to import Bedrock dependencies. "
                f"Make sure langchain-aws is installed: poetry add langchain-aws. "
                f"Error: {str(e)}"
            )
        except ValueError as e:
            # Re-raise ValueError as-is (likely from pydantic validation)
            logger.error(f"Invalid Bedrock configuration: {str(e)}")
            raise
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Failed to initialize Bedrock embeddings: {str(e)}")
            
            # Provide more specific error messages based on common issues
            if "credentials" in error_msg or "access" in error_msg or "permission" in error_msg:
                raise ValueError(
                    f"Failed to initialize Bedrock embedding provider - Authentication error. "
                    f"Make sure AWS credentials are configured via:\n"
                    f"  - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)\n"
                    f"  - IAM role (if running on EC2/Lambda)\n"
                    f"  - ~/.aws/credentials file\n"
                    f"  - Or provide aws_access_key_id and aws_secret_access_key in config\n"
                    f"Error: {str(e)}"
                )
            elif "model" in error_msg and ("not found" in error_msg or "not available" in error_msg):
                raise ValueError(
                    f"Failed to initialize Bedrock embedding provider - Model not accessible. "
                    f"Make sure:\n"
                    f"  - Model ID '{self.model_id}' is correct\n"
                    f"  - Model access is enabled in Bedrock console for your AWS account\n"
                    f"  - Region '{self.region}' supports this model\n"
                    f"Error: {str(e)}"
                )
            elif "region" in error_msg:
                raise ValueError(
                    f"Failed to initialize Bedrock embedding provider - Invalid region. "
                    f"Make sure region '{self.region}' is valid and supports Bedrock. "
                    f"Error: {str(e)}"
                )
            else:
                raise ValueError(
                    f"Failed to initialize Bedrock embedding provider. "
                    f"Make sure AWS credentials are configured (via env vars, IAM role, or ~/.aws/credentials) "
                    f"and model access is enabled in Bedrock console. "
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


class VertexAIEmbeddingProvider(BaseEmbeddingProvider):
    """Google Vertex AI embedding provider using custom wrapper"""
    
    def __init__(self):
        try:
            from app.core.vertexai_wrapper import VertexAIEmbeddings
            self.VertexAIEmbeddings = VertexAIEmbeddings
        except ImportError as e:
            raise ImportError(
                f"Failed to import VertexAIEmbeddings from vertexai_wrapper. "
                f"Make sure google-cloud-aiplatform is installed: poetry add google-cloud-aiplatform. "
                f"Error: {str(e)}"
            )
        
        self.model_id = settings.VERTEX_AI_EMBEDDING_MODEL_ID
        self.project_id = settings.VERTEX_AI_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION
        self.credentials_path = settings.VERTEX_AI_CREDENTIALS_PATH
        
        if not self.project_id:
            raise ValueError("VERTEX_AI_PROJECT_ID is required when using Vertex AI embedding provider")
        if not self.location:
            raise ValueError("VERTEX_AI_LOCATION is required when using Vertex AI embedding provider")
        if not self.model_id:
            raise ValueError("VERTEX_AI_EMBEDDING_MODEL_ID is required when using Vertex AI embedding provider")
        
        # Set dimensions based on model
        # textembedding-gecko@001 and @002 use 768 dimensions
        # textembedding-gecko@003 uses 768 dimensions
        # textembedding-gecko-multilingual@001 uses 768 dimensions
        if "textembedding-gecko" in self.model_id.lower():
            self.dimensions = 768
        else:
            # Default fallback
            self.dimensions = 768
            logger.warning(f"Unknown embedding model, defaulting to {self.dimensions} dimensions")
        
        # Initialize embeddings client
        try:
            vertexai_kwargs = {
                "model_name": self.model_id,
                "project": self.project_id,
                "location": self.location,
            }
            
            if self.credentials_path:
                vertexai_kwargs["credentials_path"] = self.credentials_path
                logger.info(f"Using service account key file for Vertex AI embeddings: {self.credentials_path}")
            else:
                logger.info("Using Application Default Credentials (ADC) for Vertex AI embeddings")
            
            self.embeddings_client = self.VertexAIEmbeddings(**vertexai_kwargs)
            logger.info(f"Initialized Vertex AI embeddings with model {self.model_id}, {self.dimensions} dimensions")
        except ImportError as e:
            logger.error(f"Failed to import Vertex AI dependencies: {str(e)}")
            raise ImportError(
                f"Failed to import Vertex AI dependencies. "
                f"Make sure google-cloud-aiplatform is installed: poetry add google-cloud-aiplatform. "
                f"Error: {str(e)}"
            )
        except ValueError as e:
            # Re-raise ValueError as-is (likely from pydantic validation or our wrapper)
            logger.error(f"Invalid Vertex AI configuration: {str(e)}")
            raise
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Failed to initialize Vertex AI embeddings: {str(e)}")
            
            # Provide more specific error messages based on common issues
            if "credentials" in error_msg or "authentication" in error_msg or "googleserviceaccount" in error_msg:
                raise ValueError(
                    f"Failed to initialize Vertex AI embedding provider - Authentication error. "
                    f"Make sure Google Cloud credentials are configured via:\n"
                    f"  - GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON\n"
                    f"  - Or provide credentials_path in config\n"
                    f"  - Or use Application Default Credentials (gcloud auth application-default login)\n"
                    f"Error: {str(e)}"
                )
            elif "404" in error_msg or "not found" in error_msg or "publisher model" in error_msg:
                raise ValueError(
                    f"Failed to initialize Vertex AI embedding provider - Model not found or not accessible. "
                    f"Make sure:\n"
                    f"  - Model ID '{self.model_id}' is correct\n"
                    f"  - Model is enabled in Vertex AI Model Garden for project '{self.project_id}'\n"
                    f"  - Vertex AI API is enabled in Google Cloud Console\n"
                    f"  - Region '{self.location}' supports this model\n"
                    f"Error: {str(e)}"
                )
            elif "api" in error_msg and ("not enabled" in error_msg or "enable" in error_msg):
                raise ValueError(
                    f"Failed to initialize Vertex AI embedding provider - API not enabled. "
                    f"Make sure Vertex AI API is enabled in Google Cloud Console for project '{self.project_id}'. "
                    f"Error: {str(e)}"
                )
            else:
                raise ValueError(
                    f"Failed to initialize Vertex AI embedding provider. "
                    f"Make sure GOOGLE_APPLICATION_CREDENTIALS is set or credentials_path is provided, "
                    f"and Vertex AI API is enabled. "
                    f"Error: {str(e)}"
                )
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate Vertex AI embedding"""
        try:
            # Use embed_query for single text
            embedding = self.embeddings_client.embed_query(text)
            
            if embedding and len(embedding) > 0:
                logger.debug(f"Generated Vertex AI embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.error("Vertex AI returned empty embedding")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Vertex AI embedding: {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate Vertex AI embeddings for multiple texts"""
        try:
            # Use embed_documents for batch
            embeddings = self.embeddings_client.embed_documents(texts)
            
            # Convert to list of Optional[List[float]]
            result = []
            for embedding in embeddings:
                if embedding and len(embedding) > 0:
                    result.append(embedding)
                else:
                    logger.warning("Received empty embedding in batch")
                    result.append(None)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating Vertex AI embeddings batch: {str(e)}")
            # Return None for all on batch failure
            return [None] * len(texts)
    
    def get_embedding_dimensions(self) -> int:
        """Get Vertex AI embedding dimensions"""
        return self.dimensions
    
    def get_model_name(self) -> str:
        """Get Vertex AI model ID"""
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
    elif provider_name == "vertexai":
        logger.info("Initializing Vertex AI embedding provider")
        return VertexAIEmbeddingProvider()
    else:
        raise ValueError(
            f"Unsupported embedding provider: {provider_name}. "
            f"Supported providers: 'openai', 'bedrock', 'vertexai'"
        )

