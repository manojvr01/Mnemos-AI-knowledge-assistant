from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM completions and streaming.
    Enables provider-independent RAG reasoning (OpenAI, Gemini, Local, Mock).
    """

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        """
        Generates a non-streaming completion.
        Returns dict with keys: 'content', 'prompt_tokens', 'completion_tokens', 'model_name'.
        """
        pass

    @abstractmethod
    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> AsyncGenerator[str, None]:
        """Yields text tokens asynchronously as they are generated."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the model being called."""
        pass
