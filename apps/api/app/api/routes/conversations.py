import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.conversation import Conversation, Message, Citation
from app.security.dependencies import get_current_user, get_current_workspace
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    SendMessageRequest,
    MessageResponse,
)
from app.rag.service import RAGService

router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: ConversationCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Create a new grounded conversation thread scoped to the active workspace."""
    conv = Conversation(
        workspace_id=workspace.id,
        user_id=current_user.id,
        title=req.title or "New Conversation",
        scope=req.scope,
        scope_id=req.scope_id,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations belonging to the user in the current workspace."""
    stmt = (
        select(Conversation)
        .where(
            Conversation.workspace_id == workspace.id,
            Conversation.user_id == current_user.id,
        )
        .order_by(Conversation.updated_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{id}", response_model=ConversationDetailResponse)
async def get_conversation(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full conversation details with messages and citations."""
    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.messages).selectinload(Message.citations)
        )
        .where(
            Conversation.id == id,
            Conversation.workspace_id == workspace.id,
        )
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.post("/{id}/messages", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def send_message(
    id: uuid.UUID,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a question in a conversation, invoke grounded RAG, validate citations,
    and persist user & assistant messages.
    """
    # 1. Fetch conversation
    stmt = select(Conversation).where(
        Conversation.id == id,
        Conversation.workspace_id == workspace.id,
    )
    conv = (await db.execute(stmt)).scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    # 2. Record user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.content,
    )
    db.add(user_msg)
    await db.commit()

    # 3. Fetch past messages for conversational context
    history_stmt = (
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
    )
    history_rows = (await db.execute(history_stmt)).scalars().all()
    chat_history = [{"role": m.role, "content": m.content} for m in history_rows[:-1]]

    # 4. Invoke Grounded RAG Pipeline
    rag_service = RAGService(db=db)
    rag_result = await rag_service.answer_question(
        workspace_id=workspace.id,
        query=req.content,
        collection_id=conv.scope_id if conv.scope == "COLLECTION" else None,
        document_id=conv.scope_id if conv.scope == "DOCUMENT" else None,
        chat_history=chat_history,
    )

    # 5. Persist assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=rag_result["content"],
        model_name=rag_result["model_name"],
        prompt_tokens=rag_result["prompt_tokens"],
        completion_tokens=rag_result["completion_tokens"],
        insufficient_evidence=rag_result["insufficient_evidence"],
    )
    db.add(assistant_msg)
    await db.flush()

    # 6. Persist citations
    saved_citations: List[Citation] = []
    for c_data in rag_result["citations"]:
        cit = Citation(
            message_id=assistant_msg.id,
            chunk_id=c_data["chunk_id"],
            document_id=c_data["document_id"],
            document_title=c_data["document_title"],
            page_number=c_data["page_number"],
            excerpt=c_data["excerpt"],
            similarity_score=c_data["similarity_score"],
        )
        db.add(cit)
        saved_citations.append(cit)

    # If first message, auto-update conversation title from question
    if len(history_rows) <= 1:
        truncated_title = req.content.strip()
        if len(truncated_title) > 60:
            truncated_title = truncated_title[:57] + "..."
        conv.title = truncated_title

    await db.commit()

    # Reload message with citations loaded for response serialization
    msg_stmt = (
        select(Message)
        .options(selectinload(Message.citations))
        .where(Message.id == assistant_msg.id)
    )
    return (await db.execute(msg_stmt)).scalar_one()
