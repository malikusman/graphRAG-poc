"""
Bedrock wrapper using boto3 directly

This module provides Bedrock integration using boto3 when langchain-community
Bedrock classes are not available or incompatible.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

logger = logging.getLogger(__name__)


class ChatBedrock(BaseChatModel):
    """Custom Bedrock chat model using boto3"""
    
    model_id: str = Field(...)
    region_name: str = Field(default="us-east-1")
    temperature: float = Field(default=0.1)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize boto3 client
        client_kwargs = {"region_name": self.region_name}
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs.update({
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key,
            })
        self.client = boto3.client("bedrock-runtime", **client_kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "bedrock"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response from Bedrock"""
        # Convert messages to Claude format
        system_prompt = ""
        messages_list = []
        
        for msg in messages:
            if hasattr(msg, 'type'):
                if msg.type == "system":
                    system_prompt = msg.content
                elif msg.type == "human":
                    messages_list.append({"role": "user", "content": msg.content})
                elif msg.type == "ai":
                    messages_list.append({"role": "assistant", "content": msg.content})
            else:
                # Fallback
                messages_list.append({"role": "user", "content": str(msg.content)})
        
        # Prepare request body for Claude models
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": self.temperature,
            "messages": messages_list
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        if stop:
            body["stop_sequences"] = stop
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text from Claude response
            text = response_body.get("content", [{}])[0].get("text", "")
            
            message = AIMessage(content=text)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            logger.error(f"Bedrock API error: {str(e)}")
            raise
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate - same as sync for now"""
        return self._generate(messages, stop, run_manager, **kwargs)


class BedrockEmbeddings:
    """Custom Bedrock embeddings using boto3"""
    
    def __init__(
        self,
        model_id: str,
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.model_id = model_id
        self.region_name = region_name
        
        # Initialize boto3 client
        client_kwargs = {"region_name": region_name}
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
            })
        self.client = boto3.client("bedrock-runtime", **client_kwargs)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        embeddings = []
        for text in texts:
            embedding = self._embed_query(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self._embed_query(text)
    
    def _embed_query(self, text: str) -> List[float]:
        """Internal method to embed text using Titan embeddings"""
        # Titan embeddings format
        body = json.dumps({"inputText": text})
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            return embedding
            
        except Exception as e:
            logger.error(f"Bedrock embedding error: {str(e)}")
            raise

