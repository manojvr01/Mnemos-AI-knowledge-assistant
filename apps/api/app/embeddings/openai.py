import httpx
from typing import List
from app.embeddings.base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embeddings provider (e.g. text-embedding-3-small, text-embedding-3-large).
    Calls OpenAI's REST API using httpx async client.
    """

    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small", dimension: int = 1536):
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be provided to use OpenAIEmbeddingProvider.")
        self.api_key = api_key
        self._model_name = model_name
        self._dimension = dimension
        self.endpoint = "https://api.openai.com/v1/embeddings"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self._model_name,
            "dimensions": self._dimension
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI embedding error ({resp.status_code}): {resp.text}")
            data = resp.json()
            return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]

    async def embed_query(self, text: str) -> List[float]:
        results = await self.embed_texts([text])
        return results[0]
