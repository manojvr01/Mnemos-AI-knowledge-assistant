from app.core.config import settings
from app.embeddings.base import BaseEmbeddingProvider
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.openai import OpenAIEmbeddingProvider
from app.embeddings.gemini import GeminiEmbeddingProvider

_provider_instance: BaseEmbeddingProvider | None = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """
    Factory function returning the configured embedding provider singleton.
    Can be dynamically overridden in tests via set_embedding_provider().
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_type = settings.EMBEDDING_PROVIDER.lower().strip()

    if provider_type == "openai":
        _provider_instance = OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIMENSION
        )
    elif provider_type == "gemini":
        _provider_instance = GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIMENSION
        )
    else:
        _provider_instance = MockEmbeddingProvider(
            model_name=settings.EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIMENSION
        )

    return _provider_instance


def set_embedding_provider(provider: BaseEmbeddingProvider | None) -> None:
    """Explicitly set or reset the embedding provider (useful for test fixtures)."""
    global _provider_instance
    _provider_instance = provider
