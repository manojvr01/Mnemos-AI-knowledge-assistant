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
from app.tests.test_ingestion import create_sample_pdf_bytes, create_sample_docx_bytes


@pytest.fixture(autouse=True)
def setup_e2e_mocks():
    """Ensure deterministic embedding and LLM providers for end-to-end integration."""
    set_embedding_provider(MockEmbeddingProvider())
    set_llm_provider(MockLLMProvider())
    yield
    set_embedding_provider(None)
    set_llm_provider(None)


@pytest.mark.asyncio
async def test_full_rag_lifecycle_e2e(async_client: AsyncClient, db_session):
    """
    End-to-End integration test validating complete user journey:
    1. Register user -> Automatic workspace provisioning
    2. Upload paginated PDF document
    3. Ingest document -> PyMuPDF page parsing -> Recursive chunking -> Embedding generation
    4. Verify document status polling endpoint
    5. Execute semantic search query -> Cosine scoring
    6. Initiate chat conversation thread
    7. Submit grounded question -> RAG retrieval -> Anti-hallucination prompt -> Answer generation
    8. Validate citation extraction -> Document name, Page number, Excerpt
    9. Fetch source content directly from document content endpoint
    10. Delete document -> Cascade deletion of chunks and physical file
    """
    # 1. Register User
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "lifecycle_analyst@mnemos.ai", "password": "Password123!"}
    )
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert "id" in user_data["user"]
    assert "id" in user_data["workspace"]

    # 2. Upload Paginated PDF
    p1 = "Google Antigravity IDE connects directly with development tools and knowledge sources."
    p2 = "Model Context Protocol connects AI assistants with tools and knowledge sources."
    pdf_bytes = create_sample_pdf_bytes([p1, p2])
    files = {"file": ("antigravity_overview.pdf", pdf_bytes, "application/pdf")}

    upload_res = await async_client.post("/api/v1/documents", files=files)
    assert upload_res.status_code == 202
    doc_id = upload_res.json()["id"]

    # 3. Process Ingestion Pipeline
    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await process_document_ingestion(doc.id, doc.storage_key, doc.mime_type)

    # 4. Verify Document Status
    status_res = await async_client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "INDEXED"
    assert status_data["page_count"] == 2
    assert status_data["chunk_count"] >= 2

    # 5. Semantic Search Endpoint
    search_res = await async_client.post(
        "/api/v1/search",
        json={"query": "Google Antigravity IDE development tools", "top_k": 3}
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total_results"] >= 1
    assert search_data["results"][0]["page_number"] == 1
    assert search_data["results"][0]["document_title"] == "antigravity_overview.pdf"

    # 6. Create Conversation Thread
    conv_res = await async_client.post(
        "/api/v1/conversations",
        json={"title": "Antigravity E2E Thread", "scope": "WORKSPACE"}
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 7. Ask Grounded Question
    msg_res = await async_client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "How does Google Antigravity IDE connect with development tools?"}
    )
    assert msg_res.status_code == 200
    msg_data = msg_res.json()
    assert msg_data["role"] == "assistant"
    assert msg_data["insufficient_evidence"] is False
    assert len(msg_data["citations"]) >= 1

    # 8. Validate Citation Metadata
    cit = msg_data["citations"][0]
    assert cit["document_title"] == "antigravity_overview.pdf"
    assert cit["page_number"] == 1
    assert "Google Antigravity IDE" in cit["excerpt"]
    assert cit["similarity_score"] is not None

    # 9. Verify Source Viewer / Content Endpoint
    content_res = await async_client.get(f"/api/v1/documents/{doc_id}/content?page_number=1")
    assert content_res.status_code == 200
    assert "Google Antigravity IDE" in content_res.json()["content"]

    # 10. Clean Deletion
    del_res = await async_client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200

    # Confirm document no longer exists
    get_res = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 404
