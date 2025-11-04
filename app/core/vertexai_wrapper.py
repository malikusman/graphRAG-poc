"""
Custom LangChain-compatible wrappers for Google Vertex AI

These wrappers use google-cloud-aiplatform SDK directly to avoid
dependency conflicts with langchain-google-vertexai package.
"""

import logging
import os
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Sequence

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.chat_models import (
    agenerate_from_stream,
    generate_from_stream,
)
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.embeddings import Embeddings
from pydantic import Field

logger = logging.getLogger(__name__)


class ChatVertexAI(BaseChatModel):
    """
    Custom LangChain wrapper for Google Vertex AI Generative Models
    
    Uses google-cloud-aiplatform SDK directly to avoid dependency conflicts.
    """

    model_name: str = Field(default="gemini-pro")
    temperature: float = Field(default=0.1)
    project: str = Field(...)
    location: str = Field(default="us-central1")
    credentials_path: Optional[str] = Field(default=None)
    max_tokens: Optional[int] = Field(default=None)
    top_p: Optional[float] = Field(default=None)
    top_k: Optional[int] = Field(default=None)
    stop: Optional[List[str]] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize Vertex AI
        try:
            import vertexai
            
            # Set credentials if provided
            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                logger.info(f"Using credentials from: {self.credentials_path}")
            
            # Initialize Vertex AI
            vertexai.init(project=self.project, location=self.location)
            logger.info(f"Initialized Vertex AI with project={self.project}, location={self.location}")
        except ImportError:
            raise ImportError(
                "google-cloud-aiplatform is required. Install it with: poetry add google-cloud-aiplatform"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            raise ValueError(
                f"Failed to initialize Vertex AI. "
                f"Make sure GOOGLE_APPLICATION_CREDENTIALS is set or credentials_path is provided. "
                f"Error: {str(e)}"
            )

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "vertexai"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "project": self.project,
            "location": self.location,
            "max_tokens": self.max_tokens,
        }

    def _convert_messages_to_gemini_format(
        self, messages: Sequence[BaseMessage]
    ) -> tuple:
        """
        Convert LangChain messages to Gemini format.
        
        Returns:
            Tuple of (system_instruction, history) where history is list of
            {"role": "user"/"model", "parts": [{"text": "..."}]}
        """
        from vertexai.preview.generative_models import Content, Part

        system_instruction = None
        history = []

        for message in messages:
            if isinstance(message, SystemMessage):
                # System messages become system_instruction in Gemini
                if system_instruction is None:
                    system_instruction = message.content
                else:
                    # Append if multiple system messages
                    system_instruction += "\n" + message.content
            elif isinstance(message, HumanMessage):
                history.append({"role": "user", "parts": [{"text": message.content}]})
            elif isinstance(message, AIMessage):
                history.append({"role": "model", "parts": [{"text": message.content}]})

        return system_instruction, history

    def _convert_gemini_response_to_message(
        self, response: Any
    ) -> AIMessage:
        """Convert Gemini response to LangChain AIMessage."""
        # Extract text from response
        # Chat response from send_message has .text attribute
        # generate_content response has .candidates
        if hasattr(response, "text") and response.text:
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            # Extract from candidates
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                text = candidate.content.parts[0].text
            elif hasattr(candidate, "text"):
                text = candidate.text
            else:
                text = str(candidate)
        elif isinstance(response, str):
            text = response
        else:
            # Try to extract from various response formats
            text = str(response)
            logger.warning(f"Unexpected response format: {type(response)}, trying to extract text")

        return AIMessage(content=text)

    def _generate(
        self,
        messages: Sequence[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat completion synchronously."""
        try:
            from vertexai.preview.generative_models import GenerationConfig, GenerativeModel

            # Convert messages to Gemini format
            system_instruction, history = self._convert_messages_to_gemini_format(messages)

            # Build generation config
            generation_config_params = {
                "temperature": self.temperature,
            }
            
            if self.max_tokens:
                generation_config_params["max_output_tokens"] = self.max_tokens
            if self.top_p:
                generation_config_params["top_p"] = self.top_p
            if self.top_k:
                generation_config_params["top_k"] = self.top_k
            
            # Use stop from parameter or instance
            stop_sequences = stop or self.stop
            if stop_sequences:
                generation_config_params["stop_sequences"] = stop_sequences

            generation_config = GenerationConfig(**generation_config_params)

            # Initialize model
            model = GenerativeModel(self.model_name)

            # Prepare model kwargs
            model_kwargs = {"generation_config": generation_config}
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction

            # Generate response
            # Get the last user message content for generation
            last_user_msg = next((msg for msg in messages if isinstance(msg, HumanMessage)), None)
            if not last_user_msg:
                raise ValueError("No user message found in messages")
            
            # Build conversation history if needed
            if len(history) > 1:
                # Multi-turn conversation - use start_chat with history
                from vertexai.preview.generative_models import Content, Part
                
                # Build history as Content objects
                chat_history = []
                for msg in history[:-1]:  # Exclude last user message
                    if msg["role"] == "user":
                        chat_history.append(
                            Content(role="user", parts=[Part(text=msg["parts"][0]["text"])])
                        )
                    elif msg["role"] == "model":
                        chat_history.append(
                            Content(role="model", parts=[Part(text=msg["parts"][0]["text"])])
                        )
                
                # Start chat with history
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(
                    last_user_msg.content,
                    generation_config=generation_config,
                )
            else:
                # Simple single message
                # Initialize model with system instruction if provided
                if system_instruction:
                    model_with_system = GenerativeModel(
                        self.model_name,
                        system_instruction=system_instruction
                    )
                else:
                    model_with_system = model
                
                response = model_with_system.generate_content(
                    last_user_msg.content,
                    generation_config=generation_config,
                )

            # Convert response to AIMessage
            ai_message = self._convert_gemini_response_to_message(response)

            # Create ChatResult
            generation = ChatGeneration(message=ai_message)
            return ChatResult(generations=[generation])

        except Exception as e:
            logger.error(f"Error generating Vertex AI response: {str(e)}")
            raise ValueError(f"Failed to generate response from Vertex AI: {str(e)}")

    async def _agenerate(
        self,
        messages: Sequence[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a chat completion asynchronously."""
        # For now, use synchronous version (Vertex AI SDK may support async later)
        # In production, you might want to run this in a thread pool
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._generate(messages, stop=stop, run_manager=None, **kwargs),
        )


class VertexAIEmbeddings(Embeddings):
    """
    Custom LangChain wrapper for Google Vertex AI Text Embeddings
    
    Uses google-cloud-aiplatform SDK directly to avoid dependency conflicts.
    """

    def __init__(
        self,
        model_name: str = "textembedding-gecko@003",
        project: str = None,
        location: str = "us-central1",
        credentials_path: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model_name = model_name
        self.project = project
        self.location = location
        self.credentials_path = credentials_path
        
        # Initialize Vertex AI
        try:
            import vertexai
            from vertexai.preview.language_models import TextEmbeddingModel
            
            # Set credentials if provided
            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
                logger.info(f"Using credentials from: {self.credentials_path}")
            
            # Initialize Vertex AI
            vertexai.init(project=self.project, location=self.location)
            logger.info(f"Initialized Vertex AI embeddings with project={self.project}, location={self.location}")
            
            # Cache the model instance to avoid re-instantiation on every call
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            logger.debug(f"Cached TextEmbeddingModel instance for {self.model_name}")
        except ImportError:
            raise ImportError(
                "google-cloud-aiplatform is required. Install it with: poetry add google-cloud-aiplatform"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            raise ValueError(
                f"Failed to initialize Vertex AI. "
                f"Make sure GOOGLE_APPLICATION_CREDENTIALS is set or credentials_path is provided. "
                f"Error: {str(e)}"
            )

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        try:
            # Use cached model instance
            embeddings = self.model.get_embeddings([text])
            
            if embeddings and len(embeddings) > 0:
                # Extract embedding vector
                embedding = embeddings[0].values
                logger.debug(f"Generated Vertex AI embedding with {len(embedding)} dimensions")
                return embedding
            else:
                logger.error("Vertex AI returned empty embedding")
                return []

        except Exception as e:
            logger.error(f"Error generating Vertex AI embedding: {str(e)}")
            raise ValueError(f"Failed to generate embedding from Vertex AI: {str(e)}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        try:
            # Use cached model instance
            embeddings = self.model.get_embeddings(texts)
            
            # Convert to list of lists
            result = []
            for embedding in embeddings:
                if embedding and hasattr(embedding, "values"):
                    result.append(embedding.values)
                else:
                    logger.warning("Received empty embedding")
                    result.append([])
            
            logger.debug(f"Generated {len(result)} Vertex AI embeddings")
            return result

        except Exception as e:
            logger.error(f"Error generating Vertex AI embeddings batch: {str(e)}")
            raise ValueError(f"Failed to generate embeddings from Vertex AI: {str(e)}")

