from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """
    Abstract interface for embedding generation.
    Enables provider-agnostic embeddings (OpenAI, Gemini, Local, Mock).
    """

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate a vector embedding for a single search query."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name/identifier of the embedding model."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality (e.g. 1536)."""
        pass
