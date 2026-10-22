import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    id: uuid.UUID
    chunk_id: Optional[uuid.UUID]
    document_id: uuid.UUID
    document_title: str
    page_number: Optional[int]
    excerpt: str
    similarity_score: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    model_name: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    insufficient_evidence: bool
    citations: List[CitationResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    title: Optional[str] = Field("New Conversation", max_length=255)
    scope: str = Field("WORKSPACE", pattern="^(WORKSPACE|DOCUMENT|COLLECTION)$")
    scope_id: Optional[uuid.UUID] = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    scope: str
    scope_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
