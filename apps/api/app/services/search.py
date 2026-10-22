import uuid
import math
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentChunk
from app.models.collection import DocumentCollection
from app.schemas.search import SearchResultChunk
from app.embeddings.factory import get_embedding_provider
from app.core.config import settings
import re

STOPWORDS = {
    'how', 'does', 'do', 'did', 'with', 'via', 'the', 'a', 'an', 'is', 'are', 'page',
    'and', 'in', 'on', 'at', 'to', 'for', 'of', '1', '2', '3', 'what', 'who', 'from', 'can', 'will'
}


def _compute_hybrid_score(query: str, content: str, vector_score: float) -> float:
    """Combine vector semantic score with exact lexical keyword matching."""
    cleaned = query.strip().lower()
    raw_words = re.findall(r"\b\w+\b", cleaned)
    words = [w for w in raw_words if w not in STOPWORDS]
    if not words:
        words = raw_words
    if not words:
        return vector_score

    content_lower = content.lower()
    matched = 0
    for w in words:
        stem = w[:5] if len(w) > 5 else w
        if w in content_lower or stem in content_lower:
            matched += 1

    lexical_ratio = matched / len(words)
    if lexical_ratio > 0:
        boosted = 0.55 + 0.35 * lexical_ratio + 0.10 * vector_score
        return max(vector_score, boosted)
    return vector_score


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vector lists."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


class VectorSearchService:
    """
    Performs semantic vector search over document chunks.
    Guarantees strict tenant workspace isolation and optional collection filtering.
    Works natively across both PostgreSQL (with pgvector) and SQLite (in-memory test dialect).
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def search(
        self,
        workspace_id: uuid.UUID,
        query: str,
        top_k: int = 5,
        similarity_threshold: Optional[float] = None,
        collection_id: Optional[uuid.UUID] = None,
        document_id: Optional[uuid.UUID] = None,
    ) -> List[SearchResultChunk]:
        threshold = similarity_threshold if similarity_threshold is not None else settings.RAG_SIMILARITY_THRESHOLD

        # 1. Generate query vector
        query_vector = await self.embedding_provider.embed_query(query)

        # 2. Check dialect
        bind = self.db.bind
        dialect_name = bind.dialect.name if bind else "postgresql"

        # If PostgreSQL, we can utilize pgvector cosine distance operator <=>
        if dialect_name == "postgresql":
            # Cosine distance: 0 = identical, 2 = opposite. Similarity = 1 - (distance / 2) or 1 - distance (for normalized)
            # In pgvector: cosine distance <=> produces 1 - cosine_similarity for normalized vectors.
            cosine_dist = DocumentChunk.embedding.cosine_distance(query_vector)
            similarity_expr = (1.0 - cosine_dist).label("similarity")

            stmt = (
                select(
                    DocumentChunk,
                    Document.original_filename,
                    similarity_expr
                )
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(
                    DocumentChunk.workspace_id == workspace_id,
                    Document.status == "INDEXED",
                    DocumentChunk.embedding.isnot(None)
                )
            )

            if collection_id:
                stmt = stmt.join(
                    DocumentCollection,
                    DocumentCollection.document_id == Document.id
                ).where(DocumentCollection.collection_id == collection_id)

            if document_id:
                stmt = stmt.where(DocumentChunk.document_id == document_id)

            # Order by similarity descending
            stmt = stmt.order_by(cosine_dist.asc()).limit(top_k * 2)
            rows = (await self.db.execute(stmt)).all()

            results: List[SearchResultChunk] = []
            for chunk, original_filename, sim in rows:
                score = _compute_hybrid_score(query, chunk.content, float(sim))
                if score >= threshold:
                    results.append(
                        SearchResultChunk(
                            chunk_id=chunk.id,
                            document_id=chunk.document_id,
                            document_title=original_filename,
                            chunk_index=chunk.chunk_index,
                            content=chunk.content,
                            page_number=chunk.page_number,
                            start_char_offset=chunk.start_char_offset,
                            end_char_offset=chunk.end_char_offset,
                            similarity_score=round(score, 4)
                        )
                    )
                if len(results) >= top_k:
                    break

            return results

        # Fallback for SQLite / unit-test environments: in-memory cosine computation
        stmt = (
            select(DocumentChunk, Document.original_filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                DocumentChunk.workspace_id == workspace_id,
                Document.status == "INDEXED"
            )
        )

        if collection_id:
            stmt = stmt.join(
                DocumentCollection,
                DocumentCollection.document_id == Document.id
            ).where(DocumentCollection.collection_id == collection_id)

        if document_id:
            stmt = stmt.where(DocumentChunk.document_id == document_id)

        rows = (await self.db.execute(stmt)).all()

        scored_chunks: List[Tuple[DocumentChunk, str, float]] = []
        for chunk, original_filename in rows:
            chunk_vec = chunk.embedding
            if isinstance(chunk_vec, list):
                raw_score = _cosine_similarity(query_vector, chunk_vec)
            else:
                raw_score = 0.0

            score = _compute_hybrid_score(query, chunk.content, raw_score)
            if score >= threshold:
                scored_chunks.append((chunk, original_filename, score))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[2], reverse=True)

        return [
            SearchResultChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=original_filename,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                start_char_offset=chunk.start_char_offset,
                end_char_offset=chunk.end_char_offset,
                similarity_score=round(score, 4)
            )
            for chunk, original_filename, score in scored_chunks[:top_k]
        ]
