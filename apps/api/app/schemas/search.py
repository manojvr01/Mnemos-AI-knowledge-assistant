import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language search query")
    collection_id: Optional[uuid.UUID] = Field(None, description="Optional collection filter")
    document_id: Optional[uuid.UUID] = Field(None, description="Optional single document filter")
    top_k: int = Field(5, ge=1, le=50, description="Maximum number of chunks to return")
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum cosine similarity score (0.0 to 1.0)")


class SearchResultChunk(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    chunk_index: int
    content: str
    page_number: Optional[int]
    start_char_offset: Optional[int]
    end_char_offset: Optional[int]
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0, higher is better)")


class SearchResponse(BaseModel):
    query: str
    workspace_id: uuid.UUID
    total_results: int
    results: List[SearchResultChunk]
