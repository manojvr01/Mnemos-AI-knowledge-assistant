import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.document import Document
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.factory import set_embedding_provider
from app.rag.llm.mock import MockLLMProvider
from app.rag.llm.factory import set_llm_provider
from app.ingestion.pipeline import process_document_ingestion
from app.tests.test_ingestion import create_sample_pdf_bytes


@pytest.fixture(autouse=True)
def setup_rag_mocks():
    set_embedding_provider(MockEmbeddingProvider())
    set_llm_provider(MockLLMProvider())
    yield
    set_embedding_provider(None)
    set_llm_provider(None)


@pytest.mark.asyncio
async def test_grounded_conversation_with_citations(async_client: AsyncClient, db_session):
    """
    Test creating a conversation, sending a question grounded in an uploaded document,
    and receiving an answer with verified citations.
    """
    # 1. Register & Auth
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "rag_user@mnemos.ai", "password": "Password123!"}
    )

    # 2. Upload Document
    pdf_bytes = create_sample_pdf_bytes([
        "Page 1: Antigravity IDE connects directly with Google Stitch via Model Context Protocol.",
        "Page 2: Vector embeddings are indexed using PostgreSQL pgvector with HNSW."
    ])
    files = {"file": ("antigravity_guide.pdf", pdf_bytes, "application/pdf")}
    upload_res = await async_client.post("/api/v1/documents", files=files)
    assert upload_res.status_code == 202
    doc_id = upload_res.json()["id"]

    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await process_document_ingestion(doc.id, doc.storage_key, doc.mime_type)

    # 3. Create Conversation
    conv_res = await async_client.post(
        "/api/v1/conversations",
        json={"title": "Antigravity Research", "scope": "WORKSPACE"}
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 4. Ask Grounded Question
    msg_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "How does Antigravity IDE connect with Google Stitch?"}
    )
    assert msg_res.status_code == 200
    msg_data = msg_res.json()

    assert msg_data["role"] == "assistant"
    assert msg_data["insufficient_evidence"] is False
    assert len(msg_data["citations"]) >= 1

    citation = msg_data["citations"][0]
    assert citation["document_title"] == "antigravity_guide.pdf"
    assert citation["page_number"] == 1
    assert "Antigravity IDE" in citation["excerpt"]
    assert citation["similarity_score"] >= 0.5

    # 5. Retrieve Conversation Details
    detail_res = await async_client.get(f"/api/v1/conversations/{conv_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["messages"]) == 2 # 1 user + 1 assistant
    assert detail_data["messages"][1]["citations"][0]["document_title"] == "antigravity_guide.pdf"


@pytest.mark.asyncio
async def test_insufficient_evidence_refusal(async_client: AsyncClient, db_session):
    """
    Test asking a question when no relevant document exists in the workspace.
    The assistant must declare insufficient evidence without hallucinating.
    """
    # Register & Auth
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "refusal_user@mnemos.ai", "password": "Password123!"}
    )

    # Create Conversation
    conv_res = await async_client.post(
        "/api/v1/conversations",
        json={"title": "Unanswerable Question", "scope": "WORKSPACE"}
    )
    conv_id = conv_res.json()["id"]

    # Ask unanswerable question with empty workspace
    msg_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is the secret recipe for Martian sourdough bread?"}
    )
    assert msg_res.status_code == 200
    msg_data = msg_res.json()

    assert msg_data["role"] == "assistant"
    assert msg_data["insufficient_evidence"] is True
    assert "don't have enough information" in msg_data["content"].lower()
    assert len(msg_data["citations"]) == 0


@pytest.mark.asyncio
async def test_grounded_conversation_scoped_to_single_document(async_client: AsyncClient, db_session):
    """Test conversation thread strictly scoped to a single document."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "single_doc_rag@mnemos.ai", "password": "Password123!"}
    )

    pdf_doc1 = create_sample_pdf_bytes(["Microservices communicate via gRPC protocol."])
    res1 = await async_client.post("/api/v1/documents", files={"file": ("doc_grpc.pdf", pdf_doc1, "application/pdf")})
    doc_id1 = res1.json()["id"]
    doc1 = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id1)))).scalar_one()
    await process_document_ingestion(doc1.id, doc1.storage_key, doc1.mime_type)

    pdf_doc2 = create_sample_pdf_bytes(["Database clusters replicate using Raft consensus."])
    res2 = await async_client.post("/api/v1/documents", files={"file": ("doc_raft.pdf", pdf_doc2, "application/pdf")})
    doc_id2 = res2.json()["id"]
    doc2 = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id2)))).scalar_one()
    await process_document_ingestion(doc2.id, doc2.storage_key, doc2.mime_type)

    # Create conversation scoped strictly to doc1
    conv_res = await async_client.post(
        "/api/v1/conversations",
        json={"title": "gRPC Specific", "scope": "DOCUMENT", "scope_id": doc_id1}
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # Ask about Raft — should declare insufficient evidence because doc2 is out-of-scope
    msg_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "How do database clusters replicate?"}
    )
    assert msg_res.status_code == 200
    msg_data = msg_res.json()
    assert msg_data["insufficient_evidence"] is True
    assert len(msg_data["citations"]) == 0

    # Ask about gRPC — should find citation in doc1
    msg_res2 = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "How do microservices communicate via gRPC protocol?"}
    )
    assert msg_res2.status_code == 200
    msg_data2 = msg_res2.json()
    assert msg_data2["insufficient_evidence"] is False
    assert len(msg_data2["citations"]) >= 1
    assert msg_data2["citations"][0]["document_title"] == "doc_grpc.pdf"

