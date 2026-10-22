import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document, DocumentChunk
from app.models.ingestion_job import IngestionJob
from app.schemas.document import DocumentResponse, DocumentStatusResponse, DocumentDetailResponse, DocumentChunkResponse
from app.security.dependencies import get_current_user, get_current_workspace
from app.storage import get_storage
from app.ingestion.validator import validate_file, MAX_FILE_SIZE_BYTES
from app.ingestion.pipeline import process_document_ingestion

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF, DOCX, or TXT file to private storage and trigger asynchronous ingestion.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    # Read content in chunks to prevent memory spikes
    content = bytearray()
    chunk_size = 64 * 1024  # 64 KB
    while chunk := await file.read(chunk_size):
        content.extend(chunk)
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum permitted size of 50 MB.",
            )

    content_bytes = bytes(content)

    # Validate extension, magic signature, and hash
    try:
        mime_type, sha256_hash = validate_file(file.filename, content_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check for duplicate document in workspace
    dup_stmt = select(Document).where(
        Document.workspace_id == workspace.id,
        Document.content_hash == sha256_hash,
        Document.status != "FAILED"
    )
    existing_doc = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing_doc:
        raise HTTPException(
            status_code=409,
            detail=f"This exact document has already been uploaded as '{existing_doc.original_filename}'.",
        )

    # Generate safe UUID storage key (never trust raw filename as path)
    doc_id = uuid.uuid4()
    storage_key = f"workspaces/{workspace.id}/docs/{doc_id}.bin"

    # Save to private storage
    storage = get_storage()
    await storage.save_file(storage_key, content_bytes)

    # Create document record
    document = Document(
        id=doc_id,
        workspace_id=workspace.id,
        uploader_id=user.id,
        original_filename=file.filename,
        storage_key=storage_key,
        mime_type=mime_type,
        file_size_bytes=len(content_bytes),
        content_hash=sha256_hash,
        status="PENDING",
    )
    db.add(document)

    # Create ingestion job
    job = IngestionJob(
        document_id=doc_id,
        status="PENDING",
        stage="QUEUED",
    )
    db.add(job)
    await db.commit()
    await db.refresh(document)

    # Trigger async background ingestion
    background_tasks.add_task(
        process_document_ingestion,
        document_id=doc_id,
        storage_key=storage_key,
        mime_type=mime_type,
    )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    status_filter: str | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """List all documents belonging strictly to the active workspace."""
    stmt = (
        select(Document)
        .where(Document.workspace_id == workspace.id)
        .order_by(desc(Document.created_at))
        .offset(skip)
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(Document.status == status_filter.upper())

    result = await db.execute(stmt)
    documents = result.scalars().all()
    return [DocumentResponse.model_validate(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full details of a specific document within the active workspace."""
    stmt = (
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id, Document.workspace_id == workspace.id)
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_data = [
        DocumentChunkResponse.model_validate(c) for c in doc.chunks
    ]
    detail = DocumentDetailResponse.model_validate(doc)
    detail.chunks = chunks_data
    detail.chunk_count = len(chunks_data)
    return detail


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Fast polling endpoint to track document ingestion progress."""
    stmt = select(Document).where(Document.id == document_id, Document.workspace_id == workspace.id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    count_stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
    chunk_count = (await db.execute(count_stmt)).scalar() or 0

    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        page_count=doc.page_count,
        chunk_count=chunk_count,
        error=doc.error_message,
    )


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: uuid.UUID,
    page_number: int | None = Query(default=None),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve text content for a document or specific page."""
    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id, DocumentChunk.workspace_id == workspace.id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    if page_number is not None:
        stmt = stmt.where(DocumentChunk.page_number == page_number)

    chunks = (await db.execute(stmt)).scalars().all()
    if not chunks:
        # Check if doc exists
        doc = (await db.execute(select(Document).where(Document.id == document_id, Document.workspace_id == workspace.id))).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"content": "", "chunks_returned": 0}

    combined_text = "\n\n".join(c.content for c in chunks)
    return {
        "document_id": document_id,
        "page_number": page_number,
        "content": combined_text,
        "chunks_returned": len(chunks)
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Hard-delete document, chunks, and safe storage file."""
    stmt = select(Document).where(Document.id == document_id, Document.workspace_id == workspace.id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete storage file
    storage = get_storage()
    await storage.delete_file(doc.storage_key)

    # Delete from database (cascades to chunks, citations, jobs)
    await db.delete(doc)
    await db.commit()

    return {"deleted": True, "document_id": document_id}
