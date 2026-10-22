# Software Requirements Specification (SRS) — Mnemos

**Document Reference:** SRS-MNEMOS-1.0  
**Related Documents:** [PRD.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/PRD.md), [ARCHITECTURE.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/ARCHITECTURE.md), [SECURITY.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/SECURITY.md)

---

## 1. Functional Requirements

### 1.1 Authentication & Workspace Management
- **FR-AUTH-01:** System shall authenticate users using email and cryptographically hashed passwords (Argon2id or bcrypt with cost factor ≥ 12).
- **FR-AUTH-02:** System shall issue secure JSON Web Tokens (JWT) stored exclusively in `httpOnly`, `Secure`, `SameSite=Lax` cookies.
- **FR-AUTH-03:** On initial registration, system shall automatically provision a default private workspace owned by the user.
- **FR-AUTH-04:** Every subsequent authenticated request must resolve the user's active workspace and verify workspace authorization.

### 1.2 Document Ingestion & Storage
- **FR-ING-01:** System shall accept document uploads of MIME types: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, and `text/plain`.
- **FR-ING-02:** File uploads must not exceed 50 MB per file.
- **FR-ING-03:** Storage handler must validate the file header/magic bytes, generate a deterministic cryptographic SHA-256 content hash, and assign a UUID-based safe storage key (`workspaces/{ws_id}/docs/{uuid}`). Raw user filenames must never be used as filesystem paths.
- **FR-ING-04:** Document text extraction must preserve pagination for PDFs (`page_number` 1-indexed) and structure for DOCX/TXT files.
- **FR-ING-05:** Extraction failures (e.g. password protection, empty text, scanned PDFs lacking OCR) must update the document status to `FAILED` with a user-safe sanitized error message, leaving no orphan chunks.
- **FR-ING-06:** Ingestion jobs must run asynchronously via FastAPI `BackgroundTasks`, updating job records (`PENDING`, `PARSING`, `EMBEDDING`, `COMPLETED`, `FAILED`).

### 1.3 Chunking & Embeddings
- **FR-CHK-01:** Text extract must be segmented into chunks using a recursive character splitter (default 500 tokens with 10% overlap), respecting paragraph and sentence boundaries.
- **FR-CHK-02:** Each chunk must retain metadata: `document_id`, `workspace_id`, `chunk_index`, `page_number` (or `null` if unpaginated), character offsets, and token count.
- **FR-CHK-03:** Embeddings must be generated via a unified provider interface (`EmbeddingProvider`), recording `embedding_model` and `embedding_version`.
- **FR-CHK-04:** Chunks and vector embeddings must be written to PostgreSQL with pgvector within an atomic database transaction.

### 1.4 Semantic Retrieval & RAG
- **FR-RAG-01:** System shall support semantic search queries over workspace document chunks using Cosine similarity (`<=>` operator in pgvector).
- **FR-RAG-02:** Retrieval queries must enforce mandatory `workspace_id` filtering, with optional `collection_id` or `document_id` scoping. Cross-workspace retrieval must be physically prevented by SQL filter predicates.
- **FR-RAG-03:** The top-k most relevant chunks (default k=5) exceeding a similarity threshold (default 0.70) must be assembled into a bounded, untrusted context block.
- **FR-RAG-04:** The generation prompt must instruct the model to answer exclusively from the provided context passages, cite each claim with the format `[doc_id, page]`, and declare insufficient evidence if the passages do not provide the answer.
- **FR-RAG-05:** Server-side citation validator must parse generated citations, verify that every cited chunk ID exists in the retrieved set and belongs to the active workspace, and discard hallucinated citations.

### 1.5 Collections & Conversations
- **FR-COL-01:** Users can create, list, rename, and delete collections within their workspace, and assign/remove documents.
- **FR-CONV-01:** Users can create, view, list, rename, and delete chat conversations.
- **FR-CONV-02:** Messages must persist user query, assistant answer, model metadata, token usage metrics, and all validated citations.

---

## 2. Non-Functional Requirements

### 2.1 Security & Data Privacy
- **NFR-SEC-01:** Zero trust in client-supplied identifiers (`workspace_id`, `user_id`); all identities must be resolved from server-validated session claims.
- **NFR-SEC-02:** Document contents are stored in private storage (local filesystem directory with restricted OS permissions in dev; S3 private bucket with IAM restrictions in prod). Files are never publicly accessible via direct URLs.
- **NFR-SEC-03:** Ingestion documents are treated as untrusted data. Text fed into prompt templates must be delimited within explicit XML/markdown boundaries to prevent indirect prompt injection.

### 2.2 Performance & Scalability
- **NFR-PERF-01:** API health check endpoint (`/health`) response time < 20ms.
- **NFR-PERF-02:** Vector similarity query execution over 50,000 chunks < 150ms using pgvector HNSW index.
- **NFR-PERF-03:** Large file uploads must be streamed in chunks of 64KB rather than loaded entirely into memory.

### 2.3 Reliability & Fault Tolerance
- **NFR-REL-01:** Failed ingestion tasks must safely release database locks, mark records as `FAILED`, and prune partially stored artifacts.
- **NFR-REL-02:** External AI provider timeouts (embeddings and generation) must be caught gracefully, returning standardized 504/502 JSON errors without exposing stack traces.
