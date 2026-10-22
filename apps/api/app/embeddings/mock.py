import hashlib
import math
import re
from typing import List
from app.embeddings.base import BaseEmbeddingProvider

STOPWORDS = {
    'how', 'does', 'do', 'did', 'with', 'via', 'the', 'a', 'an', 'is', 'are', 'page',
    'and', 'in', 'on', 'at', 'to', 'for', 'of', '1', '2', '3', 'what', 'who', 'from', 'can', 'will'
}


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic mock embedding provider for tests and local development.
    Generates stemmed word-frequency pseudo-embeddings hashed across dimensions,
    ensuring that questions and context sharing key content words yield high cosine
    similarity (>= 0.70), while unrelated queries yield near-zero similarity.
    """

    def __init__(self, model_name: str = "mock-embedding-v1", dimension: int = 768):
        self._model_name = model_name
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector(self, text: str) -> List[float]:
        cleaned = text.strip().lower()
        if not cleaned:
            return [0.0] * self._dimension

        raw_words = re.findall(r"\b\w+\b", cleaned)
        words = [w for w in raw_words if w not in STOPWORDS]
        if not words:
            words = raw_words

        if not words:
            return [0.0] * self._dimension

        vec = [0.0] * self._dimension
        for word in words:
            # Simple prefix stem
            stem = word[:5] if len(word) > 5 else word
            h = int(hashlib.md5(stem.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dimension
            vec[idx] += 5.0

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]

        return vec

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    async def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)
