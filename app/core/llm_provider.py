"""
LLM Provider Abstraction Layer

Provides a unified interface for different LLM providers (OpenAI, Bedrock)
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
    """Amazon Bedrock LLM provider using boto3"""
    
    def __init__(self):
        try:
            from app.core.bedrock_wrapper import ChatBedrock
            self.ChatBedrock = ChatBedrock
        except ImportError as e:
            raise ImportError(
                f"Failed to import Bedrock wrapper. "
                f"Make sure boto3 is installed: poetry add boto3. "
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
        self.credentials = {}
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.credentials = {
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
            }
            logger.info("Using AWS access keys for Bedrock authentication")
        else:
            logger.info("Using IAM role or default AWS credential chain for Bedrock")
    
    def get_llm(self, temperature: float = 0.1, **kwargs) -> BaseChatModel:
        """Get Bedrock ChatBedrock instance"""
        bedrock_kwargs = {
            "model_id": self.model_id,
            "region_name": self.region,
            "temperature": temperature,
            **self.credentials,
            **kwargs
        }
        
        try:
            return self.ChatBedrock(**bedrock_kwargs)
        except Exception as e:
            logger.error(f"Failed to create Bedrock LLM: {str(e)}")
            raise ValueError(
                f"Failed to initialize Bedrock provider. "
                f"Make sure AWS credentials are configured and model access is enabled. "
                f"Error: {str(e)}"
            )
    
    def get_model_name(self) -> str:
        """Get Bedrock model ID"""
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
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: 'openai', 'bedrock'"
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

