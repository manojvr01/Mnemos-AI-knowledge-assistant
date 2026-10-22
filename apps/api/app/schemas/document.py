import uuid
from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: str
    page_count: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    page_count: int | None
    chunk_count: int
    error: str | None


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int
    content: str
    page_number: int | None
    token_count: int

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    chunks: list[DocumentChunkResponse] = []
    chunk_count: int = 0
