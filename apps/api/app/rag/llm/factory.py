from app.core.config import settings
from app.rag.llm.base import BaseLLMProvider
from app.rag.llm.mock import MockLLMProvider
from app.rag.llm.openai import OpenAILLMProvider
from app.rag.llm.gemini import GeminiLLMProvider

_llm_instance: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function returning the configured LLM provider singleton.
    Can be dynamically overridden in tests via set_llm_provider().
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    provider_type = settings.LLM_PROVIDER.lower().strip()

    if provider_type == "openai":
        _llm_instance = OpenAILLMProvider(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.LLM_MODEL,
        )
    elif provider_type == "gemini":
        _llm_instance = GeminiLLMProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.LLM_MODEL,
        )
    else:
        _llm_instance = MockLLMProvider(model_name=settings.LLM_MODEL)

    return _llm_instance


def set_llm_provider(provider: BaseLLMProvider | None) -> None:
    """Explicitly set or reset the LLM provider (useful for test fixtures)."""
    global _llm_instance
    _llm_instance = provider
