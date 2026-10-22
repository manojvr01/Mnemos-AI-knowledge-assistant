import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.document import Document
from app.embeddings.mock import MockEmbeddingProvider
from app.embeddings.factory import set_embedding_provider
from app.ingestion.pipeline import process_document_ingestion
from app.tests.test_ingestion import create_sample_pdf_bytes


@pytest.fixture(autouse=True)
def setup_mock_embeddings():
    """Ensure mock embeddings are used deterministically for tests."""
    provider = MockEmbeddingProvider()
    set_embedding_provider(provider)
    yield
    set_embedding_provider(None)


@pytest.mark.asyncio
async def test_semantic_search_success(async_client: AsyncClient, db_session):
    # 1. Register User & Auth
    auth_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "searcher@mnemos.ai", "password": "Password123!"}
    )
    assert auth_res.status_code == 201

    # 2. Upload Document
    pdf_bytes = create_sample_pdf_bytes([
        "Artificial Intelligence and Machine Learning are transforming modern industry.",
        "Deep Neural Networks and Transformers power natural language processing applications."
    ])
    files = {"file": ("ai_paper.pdf", pdf_bytes, "application/pdf")}
    upload_res = await async_client.post("/api/v1/documents", files=files)
    assert upload_res.status_code == 202
    doc_id = upload_res.json()["id"]

    # 3. Retrieve doc and ingest
    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await process_document_ingestion(doc.id, doc.storage_key, doc.mime_type)

    # 4. Search with matching query
    search_payload = {
        "query": "Artificial Intelligence and Machine Learning",
        "top_k": 5,
        "similarity_threshold": 0.5
    }
    search_res = await async_client.post("/api/v1/search", json=search_payload)
    assert search_res.status_code == 200
    data = search_res.json()

    assert data["query"] == "Artificial Intelligence and Machine Learning"
    assert data["total_results"] >= 1
    top_chunk = data["results"][0]
    assert top_chunk["document_id"] == doc_id
    assert top_chunk["document_title"] == "ai_paper.pdf"
    assert top_chunk["page_number"] == 1
    assert "Artificial Intelligence" in top_chunk["content"]
    assert top_chunk["similarity_score"] >= 0.5


@pytest.mark.asyncio
async def test_semantic_search_threshold_filtering(async_client: AsyncClient, db_session):
    # Register & Auth
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "threshold_tester@mnemos.ai", "password": "Password123!"}
    )

    pdf_bytes = create_sample_pdf_bytes(["Quantum mechanics and particle physics experiments."])
    files = {"file": ("physics.pdf", pdf_bytes, "application/pdf")}
    upload_res = await async_client.post("/api/v1/documents", files=files)
    doc_id = upload_res.json()["id"]

    doc = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id)))).scalar_one()
    await process_document_ingestion(doc.id, doc.storage_key, doc.mime_type)

    # Query with strict threshold for unrelated topic
    search_payload = {
        "query": "Culinary arts and gourmet baking recipes",
        "top_k": 5,
        "similarity_threshold": 0.99 # Impossibly high for non-exact match
    }
    search_res = await async_client.post("/api/v1/search", json=search_payload)
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["total_results"] == 0
    assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_search_workspace_tenant_isolation(async_client: AsyncClient, db_session):
    """Verify vectors in Workspace A cannot be retrieved or discovered by Workspace B."""
    # User A in Workspace A
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "user_a@mnemos.ai", "password": "Password123!"}
    )
    pdf_bytes_a = create_sample_pdf_bytes(["Confidential financial records of Corporation A."])
    files_a = {"file": ("confidential_a.pdf", pdf_bytes_a, "application/pdf")}
    upload_res_a = await async_client.post("/api/v1/documents", files=files_a)
    doc_id_a = upload_res_a.json()["id"]

    doc_a = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id_a)))).scalar_one()
    await process_document_ingestion(doc_a.id, doc_a.storage_key, doc_a.mime_type)

    # Logout User A
    await async_client.post("/api/v1/auth/logout")

    # User B in Workspace B
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "user_b@mnemos.ai", "password": "Password123!"}
    )

    # Search for User A's content as User B
    search_payload = {
        "query": "Confidential financial records of Corporation A",
        "top_k": 5,
        "similarity_threshold": 0.1
    }
    search_res = await async_client.post("/api/v1/search", json=search_payload)
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["total_results"] == 0
    assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_search_single_document_filter(async_client: AsyncClient, db_session):
    """Verify searching with document_id restricts results exclusively to that document."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "scoper@mnemos.ai", "password": "Password123!"}
    )

    # Upload Doc 1
    pdf1 = create_sample_pdf_bytes(["Document Alpha contains proprietary algorithm details."])
    res1 = await async_client.post("/api/v1/documents", files={"file": ("alpha.pdf", pdf1, "application/pdf")})
    doc_id1 = res1.json()["id"]
    doc1 = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id1)))).scalar_one()
    await process_document_ingestion(doc1.id, doc1.storage_key, doc1.mime_type)

    # Upload Doc 2
    pdf2 = create_sample_pdf_bytes(["Document Beta contains proprietary algorithm details."])
    res2 = await async_client.post("/api/v1/documents", files={"file": ("beta.pdf", pdf2, "application/pdf")})
    doc_id2 = res2.json()["id"]
    doc2 = (await db_session.execute(select(Document).where(Document.id == uuid.UUID(doc_id2)))).scalar_one()
    await process_document_ingestion(doc2.id, doc2.storage_key, doc2.mime_type)

    # Search scoped specifically to Doc 1
    search_payload = {
        "query": "proprietary algorithm",
        "document_id": doc_id1,
        "top_k": 5,
        "similarity_threshold": 0.3
    }
    search_res = await async_client.post("/api/v1/search", json=search_payload)
    assert search_res.status_code == 200
    results = search_res.json()["results"]
    assert len(results) >= 1
    assert all(r["document_id"] == doc_id1 for r in results)

