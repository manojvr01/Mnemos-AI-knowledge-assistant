import io
import uuid
from reportlab.pdfgen import canvas
import docx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.document import Document, DocumentChunk
from app.ingestion.pipeline import process_document_ingestion


def create_sample_pdf_bytes(page_texts: list[str]) -> bytes:
    """Generate in-memory multi-page PDF bytes for testing."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for text in page_texts:
        c.drawString(50, 750, text)
        c.showPage()
    c.save()
    return buf.getvalue()


def create_sample_docx_bytes(paragraphs: list[str]) -> bytes:
    """Generate in-memory DOCX bytes for testing."""
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    f = io.BytesIO()
    doc.save(f)
    return f.getvalue()


@pytest.mark.asyncio
async def test_upload_and_ingest_pdf(async_client: AsyncClient, db_session):
    # 1. Register User & Auth
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "pdf_tester@mnemos.ai", "password": "Password123!"}
    )
    assert reg_res.status_code == 201

    # 2. Synthesize a 2-page PDF
    page_1_text = "Page 1: Artificial intelligence systems require verifiable citations and ground truth."
    page_2_text = "Page 2: Modern RAG architectures utilize pgvector and deterministic similarity metrics."
    pdf_content = create_sample_pdf_bytes([page_1_text, page_2_text])

    # 3. Upload PDF
    files = {"file": ("research_paper.pdf", pdf_content, "application/pdf")}
    upload_res = await async_client.post("/api/v1/documents", files=files)
    assert upload_res.status_code == 202
    doc_data = upload_res.json()
    assert doc_data["status"] == "PENDING"
    assert doc_data["original_filename"] == "research_paper.pdf"
    doc_id = doc_data["id"]

    # 4. Execute ingestion pipeline
    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await process_document_ingestion(doc.id, doc.storage_key, doc.mime_type)

    # 5. Verify database records
    await db_session.refresh(doc)
    assert doc.status == "INDEXED"
    assert doc.page_count == 2
    assert doc.error_message is None

    chunks_stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id).order_by(DocumentChunk.chunk_index)
    chunks = (await db_session.execute(chunks_stmt)).scalars().all()
    assert len(chunks) >= 2

    # Verify page preservation
    assert chunks[0].page_number == 1
    assert "Page 1:" in chunks[0].content
    assert chunks[1].page_number == 2
    assert "Page 2:" in chunks[1].content

    # 6. Test GET /documents/{id}/status
    status_res = await async_client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "INDEXED"
    assert status_data["page_count"] == 2
    assert status_data["chunk_count"] == len(chunks)

    # 7. Test GET /documents/{id}/content
    content_res = await async_client.get(f"/api/v1/documents/{doc_id}/content?page_number=1")
    assert content_res.status_code == 200
    assert "Page 1:" in content_res.json()["content"]


@pytest.mark.asyncio
async def test_upload_and_ingest_docx(async_client: AsyncClient, db_session):
    # 1. Register & Auth
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "docx_tester@mnemos.ai", "password": "Password123!"}
    )

    # 2. Create DOCX
    docx_content = create_sample_docx_bytes([
        "Architecture Overview: Mnemos adopts a modular monorepo.",
        "Component details: Next.js frontend with FastAPI backend.",
    ])

    files = {"file": ("architecture.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = await async_client.post("/api/v1/documents", files=files)
    assert res.status_code == 202
    doc_id = res.json()["id"]

    # Ingest
    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await process_document_ingestion(doc.id, doc.storage_key, doc.mime_type)

    await db_session.refresh(doc)
    assert doc.status == "INDEXED"
    assert doc.page_count is None # Unpaginated DOCX format


@pytest.mark.asyncio
async def test_upload_and_ingest_txt(async_client: AsyncClient, db_session):
    # 1. Register & Auth
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "txt_tester@mnemos.ai", "password": "Password123!"}
    )

    txt_content = b"Plain text knowledge file with key operational notes.\nSecond line of content."
    files = {"file": ("notes.txt", txt_content, "text/plain")}
    res = await async_client.post("/api/v1/documents", files=files)
    assert res.status_code == 202
    doc_id = res.json()["id"]

    # Ingest
    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await process_document_ingestion(doc.id, doc.storage_key, doc.mime_type)

    await db_session.refresh(doc)
    assert doc.status == "INDEXED"
    assert doc.page_count is None


@pytest.mark.asyncio
async def test_reject_corrupted_magic_header(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "hacker@mnemos.ai", "password": "Password123!"}
    )

    # Spoofed PDF extension with random binary junk
    fake_pdf = b"NOT_A_PDF_MAGIC_HEADER_FAKE_DATA"
    files = {"file": ("exploit.pdf", fake_pdf, "application/pdf")}
    res = await async_client.post("/api/v1/documents", files=files)
    assert res.status_code == 400
    assert "Corrupted or invalid PDF file header" in res.json()["detail"]


@pytest.mark.asyncio
async def test_reject_empty_file(async_client: AsyncClient):
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "empty_tester@mnemos.ai", "password": "Password123!"}
    )

    files = {"file": ("empty.txt", b"", "text/plain")}
    res = await async_client.post("/api/v1/documents", files=files)
    assert res.status_code == 400
    assert "Uploaded file is empty" in res.json()["detail"]


@pytest.mark.asyncio
async def test_document_cross_workspace_isolation(async_client: AsyncClient, db_session):
    # 1. User A registers and uploads doc
    res_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "owner_a@mnemos.ai", "password": "Password123!"}
    )
    token_a = res_a.cookies.get("access_token")

    txt_content = b"Confidential document for User A only."
    files = {"file": ("confidential_a.txt", txt_content, "text/plain")}
    upload_res = await async_client.post("/api/v1/documents", files=files)
    doc_a_id = upload_res.json()["id"]

    # 2. User B registers
    res_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "intruder_b@mnemos.ai", "password": "Password123!"}
    )
    token_b = res_b.cookies.get("access_token")

    # 3. User B attempts to access User A's document -> 404 Not Found
    headers_b = {"Authorization": f"Bearer {token_b}"}
    access_res = await async_client.get(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert access_res.status_code == 404

    # 4. User B attempts to delete User A's document -> 404 Not Found
    delete_res = await async_client.delete(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    assert delete_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_success(async_client: AsyncClient, db_session):
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "deleter@mnemos.ai", "password": "Password123!"}
    )

    files = {"file": ("to_delete.txt", b"Temporary file to delete.", "text/plain")}
    upload_res = await async_client.post("/api/v1/documents", files=files)
    doc_id = upload_res.json()["id"]

    # Delete
    del_res = await async_client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # Check 404 after deletion
    check_res = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert check_res.status_code == 404
