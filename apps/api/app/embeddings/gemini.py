import httpx
from typing import List
from app.embeddings.base import BaseEmbeddingProvider


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Google Gemini embedding provider (gemini-embedding-001).
    Uses Google AI Studio Generative Language REST API.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-embedding-001", dimension: int = 768):
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided to use GeminiEmbeddingProvider.")
        self.api_key = api_key
        self._model_name = model_name
        self._dimension = dimension
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:embedContent"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        url = f"{self.endpoint}?key={self.api_key}"
        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for t in texts:
                body = {
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self._dimension
                }
                resp = await client.post(url, json=body)
                if resp.status_code != 200:
                    raise RuntimeError(f"Gemini embedding error ({resp.status_code}): {resp.text}")
                data = resp.json()
                results.append(data["embedding"]["values"])
        return results

    async def embed_query(self, text: str) -> List[float]:
        results = await self.embed_texts([text])
        return results[0]
