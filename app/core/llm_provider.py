"""
LLM Provider Abstraction Layer

Provides a unified interface for different LLM providers (OpenAI, Bedrock, Vertex AI)
to allow easy switching between providers via configuration.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def get_llm(self, temperature: float = 0.1, **kwargs) -> BaseChatModel:
        """
        Get an LLM instance configured for this provider
        
        Args:
            temperature: Temperature for model responses
            **kwargs: Additional provider-specific parameters
            
        Returns:
            BaseChatModel instance
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name/ID for this provider"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider using ChatOpenAI"""
    
    # Models that don't support temperature parameter (GPT-5 series)
    MODELS_WITHOUT_TEMPERATURE = [
        "gpt-5",
        "gpt-5-nano",
        "gpt-5-mini",
        "gpt-5-pro",
        "gpt-5-codex",
        "gpt-5-chat-latest"
    ]
    
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.api_key = settings.OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
    
    def _supports_temperature(self) -> bool:
        """Check if the current model supports temperature parameter"""
        model_lower = self.model.lower()
        # Check if model starts with any of the non-temperature models
        return not any(model_lower.startswith(no_temp_model) for no_temp_model in self.MODELS_WITHOUT_TEMPERATURE)
    
    def get_llm(self, temperature: float = 0.1, **kwargs) -> BaseChatModel:
        """Get OpenAI ChatOpenAI instance"""
        llm_kwargs = {
            "model": self.model,
            "api_key": self.api_key,
            **kwargs
        }
        
        # Only add temperature if the model supports it
        if self._supports_temperature():
            llm_kwargs["temperature"] = temperature
            logger.debug(f"Using temperature={temperature} for model {self.model}")
        else:
            logger.info(f"Model {self.model} does not support temperature parameter, omitting it")
        
        return ChatOpenAI(**llm_kwargs)
    
    def get_model_name(self) -> str:
        """Get OpenAI model name"""
        return self.model


class BedrockProvider(BaseLLMProvider):
    """Amazon Bedrock LLM provider using official langchain-aws package"""
    
    def __init__(self):
        try:
            from langchain_aws import ChatBedrock
            self.ChatBedrock = ChatBedrock
        except ImportError as e:
            raise ImportError(
                f"Failed to import ChatBedrock from langchain-aws. "
                f"Make sure langchain-aws is installed: poetry add langchain-aws. "
                f"Error: {str(e)}"
            )
        
        self.model_id = settings.BEDROCK_MODEL_ID
        self.region = settings.BEDROCK_REGION
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        
        # Validate credentials (at least region and model_id required)
        if not self.region:
            raise ValueError("BEDROCK_REGION is required when using Bedrock provider")
        if not self.model_id:
            raise ValueError("BEDROCK_MODEL_ID is required when using Bedrock provider")
        
        # Credentials can be provided via env vars, IAM role, or access keys
        # If access keys are provided, use them; otherwise rely on IAM role/default chain
        if self.aws_access_key_id and self.aws_secret_access_key:
            logger.info("Using AWS access keys for Bedrock authentication")
        else:
            logger.info("Using IAM role or default AWS credential chain for Bedrock")
    
    def get_llm(self, temperature: float = 0.1, **kwargs) -> BaseChatModel:
        """Get Bedrock ChatBedrock instance from langchain-aws"""
        from pydantic import SecretStr
        
        bedrock_kwargs = {
            "model_id": self.model_id,
            "region_name": self.region,
            "model_kwargs": {"temperature": temperature},
            **kwargs
        }
        
        # Add credentials if provided (langchain-aws uses SecretStr)
        if self.aws_access_key_id and self.aws_secret_access_key:
            bedrock_kwargs["aws_access_key_id"] = SecretStr(self.aws_access_key_id)
            bedrock_kwargs["aws_secret_access_key"] = SecretStr(self.aws_secret_access_key)
        
        try:
            return self.ChatBedrock(**bedrock_kwargs)
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
            logger.error(f"Failed to create Bedrock LLM: {str(e)}")
            
            # Provide more specific error messages based on common issues
            if "credentials" in error_msg or "access" in error_msg or "permission" in error_msg:
                raise ValueError(
                    f"Failed to initialize Bedrock provider - Authentication error. "
                    f"Make sure AWS credentials are configured via:\n"
                    f"  - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)\n"
                    f"  - IAM role (if running on EC2/Lambda)\n"
                    f"  - ~/.aws/credentials file\n"
                    f"  - Or provide aws_access_key_id and aws_secret_access_key in config\n"
                    f"Error: {str(e)}"
                )
            elif "model" in error_msg and ("not found" in error_msg or "not available" in error_msg):
                raise ValueError(
                    f"Failed to initialize Bedrock provider - Model not accessible. "
                    f"Make sure:\n"
                    f"  - Model ID '{self.model_id}' is correct\n"
                    f"  - Model access is enabled in Bedrock console for your AWS account\n"
                    f"  - Region '{self.region}' supports this model\n"
                    f"Error: {str(e)}"
                )
            elif "region" in error_msg:
                raise ValueError(
                    f"Failed to initialize Bedrock provider - Invalid region. "
                    f"Make sure region '{self.region}' is valid and supports Bedrock. "
                    f"Error: {str(e)}"
                )
            else:
                raise ValueError(
                    f"Failed to initialize Bedrock provider. "
                    f"Make sure AWS credentials are configured (via env vars, IAM role, or ~/.aws/credentials) "
                    f"and model access is enabled in Bedrock console. "
                    f"Error: {str(e)}"
                )
    
    def get_model_name(self) -> str:
        """Get Bedrock model ID"""
        return self.model_id


class VertexAIProvider(BaseLLMProvider):
    """Google Vertex AI LLM provider using custom wrapper"""
    
    def __init__(self):
        try:
            from app.core.vertexai_wrapper import ChatVertexAI
            self.ChatVertexAI = ChatVertexAI
        except ImportError as e:
            raise ImportError(
                f"Failed to import ChatVertexAI from vertexai_wrapper. "
                f"Make sure google-cloud-aiplatform is installed: poetry add google-cloud-aiplatform. "
                f"Error: {str(e)}"
            )
        
        self.model_id = settings.VERTEX_AI_MODEL_ID
        self.project_id = settings.VERTEX_AI_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION
        self.credentials_path = settings.VERTEX_AI_CREDENTIALS_PATH
        
        # Validate required settings
        if not self.project_id:
            raise ValueError("VERTEX_AI_PROJECT_ID is required when using Vertex AI provider")
        if not self.location:
            raise ValueError("VERTEX_AI_LOCATION is required when using Vertex AI provider")
        if not self.model_id:
            raise ValueError("VERTEX_AI_MODEL_ID is required when using Vertex AI provider")
        
        if self.credentials_path:
            logger.info(f"Using service account key file for Vertex AI authentication: {self.credentials_path}")
        else:
            logger.info("Using Application Default Credentials (ADC) for Vertex AI authentication")
    
    def get_llm(self, temperature: float = 0.1, **kwargs) -> BaseChatModel:
        """Get Vertex AI ChatVertexAI instance"""
        vertexai_kwargs = {
            "model_name": self.model_id,
            "temperature": temperature,
            "project": self.project_id,
            "location": self.location,
            **kwargs
        }
        
        # Add credentials path if provided
        if self.credentials_path:
            vertexai_kwargs["credentials_path"] = self.credentials_path
        
        try:
            return self.ChatVertexAI(**vertexai_kwargs)
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
            logger.error(f"Failed to create Vertex AI LLM: {str(e)}")
            
            # Provide more specific error messages based on common issues
            if "credentials" in error_msg or "authentication" in error_msg or "googleserviceaccount" in error_msg:
                raise ValueError(
                    f"Failed to initialize Vertex AI provider - Authentication error. "
                    f"Make sure Google Cloud credentials are configured via:\n"
                    f"  - GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to service account JSON\n"
                    f"  - Or provide credentials_path in config\n"
                    f"  - Or use Application Default Credentials (gcloud auth application-default login)\n"
                    f"Error: {str(e)}"
                )
            elif "404" in error_msg or "not found" in error_msg or "publisher model" in error_msg:
                raise ValueError(
                    f"Failed to initialize Vertex AI provider - Model not found or not accessible. "
                    f"Make sure:\n"
                    f"  - Model ID '{self.model_id}' is correct\n"
                    f"  - Model is enabled in Vertex AI Model Garden for project '{self.project_id}'\n"
                    f"  - Vertex AI API is enabled in Google Cloud Console\n"
                    f"  - Region '{self.location}' supports this model\n"
                    f"Error: {str(e)}"
                )
            elif "api" in error_msg and ("not enabled" in error_msg or "enable" in error_msg):
                raise ValueError(
                    f"Failed to initialize Vertex AI provider - API not enabled. "
                    f"Make sure Vertex AI API is enabled in Google Cloud Console for project '{self.project_id}'. "
                    f"Error: {str(e)}"
                )
            else:
                raise ValueError(
                    f"Failed to initialize Vertex AI provider. "
                    f"Make sure GOOGLE_APPLICATION_CREDENTIALS is set or credentials_path is provided, "
                    f"and Vertex AI API is enabled. "
                    f"Error: {str(e)}"
                )
    
    def get_model_name(self) -> str:
        """Get Vertex AI model ID"""
        return self.model_id


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function to get the appropriate LLM provider based on configuration
    
    Returns:
        BaseLLMProvider instance
        
    Raises:
        ValueError: If provider is not supported or not configured correctly
    """
    provider_name = settings.LLM_PROVIDER.lower()
    
    if provider_name == "openai":
        logger.info("Initializing OpenAI LLM provider")
        return OpenAIProvider()
    elif provider_name == "bedrock":
        logger.info("Initializing Bedrock LLM provider")
        return BedrockProvider()
    elif provider_name == "vertexai":
        logger.info("Initializing Vertex AI LLM provider")
        return VertexAIProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: 'openai', 'bedrock', 'vertexai'"
        )


def get_llm(temperature: float = 0.1, **kwargs) -> BaseChatModel:
    """
    Convenience function to get an LLM instance directly
    
    Args:
        temperature: Temperature for model responses
        **kwargs: Additional provider-specific parameters
        
    Returns:
        BaseChatModel instance configured for the selected provider
    """
    provider = get_llm_provider()
    return provider.get_llm(temperature=temperature, **kwargs)

