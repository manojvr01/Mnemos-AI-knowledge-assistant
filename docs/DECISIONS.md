# Architecture Decision Records (ADRs) — Mnemos

**Document Reference:** ADR-MNEMOS-1.0  
**Related Documents:** [ARCHITECTURE.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/ARCHITECTURE.md), [DATABASE_DESIGN.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/DATABASE_DESIGN.md)

---

## ADR-001: Monorepo Architecture with Dedicated Apps
- **Context:** Mnemos requires tight coordination between the Next.js frontend client and the FastAPI backend, while maintaining clean separation of concerns and independent deployments.
- **Decision:** Adopt a monorepo structure with `apps/web/` and `apps/api/`, alongside shared `docs/` and root `docker-compose.yml`.
- **Consequences:** Simplifies local orchestration and cross-discipline debugging; eliminates multi-repo sync overhead without requiring heavy tooling for MVP.

---

## ADR-002: PostgreSQL + pgvector vs. Standalone Vector Databases (Pinecone/Milvus/Qdrant)
- **Context:** Semantic retrieval requires storing and indexing dense vector embeddings alongside relational metadata (users, workspaces, documents, permissions, collections, conversations).
- **Decision:** Use PostgreSQL with the `pgvector` extension.
- **Rationale:**
  1. **Atomic Transactions:** Document chunks and vectors can be inserted or deleted in the exact same database transaction as document records.
  2. **Zero Split-Brain State:** Eliminates consistency lag and sync errors between an external vector store and an application SQL database.
  3. **Multi-Tenant Filtering:** Standard SQL `WHERE workspace_id = :ws_id` filters are applied natively during vector nearest-neighbor search, eliminating post-filtering overhead and security leakage.
  4. **Cost & Operational Simplicity:** One database system to backup, migrate, and maintain.

---

## ADR-003: FastAPI BackgroundTasks vs. Distributed Message Queues (Celery/RabbitMQ)
- **Context:** Ingestion of documents (parsing, chunking, embedding) takes several seconds and should not block HTTP request threads.
- **Decision:** Use FastAPI's native `BackgroundTasks` for MVP ingestion rather than introducing Celery, Redis, or RabbitMQ.
- **Rationale:** Minimizes operational complexity and infrastructure overhead. Each task runs in the background of the FastAPI event loop, updating persistent `ingestion_jobs` records in PostgreSQL. If workload scales post-MVP, the ingestion service interface is designed to seamlessly swap to an external worker.

---

## ADR-004: Strict Server-Side Citation Validation
- **Context:** Large language models can hallucinate citation markers (e.g. referencing pages or documents that were never in the context window).
- **Decision:** Implement a deterministic, server-side `CitationValidator` in the backend RAG pipeline.
- **Rationale:** When an answer is synthesized, the validator parses the cited indices, matches them against the exact chunk IDs retrieved for that specific query, and ensures they belong to the active workspace. Any invalid or fabricated citation is stripped or causes the query to declare insufficient evidence.

---

## ADR-005: httpOnly Cookies for JWT Authentication
- **Context:** Client-side token storage (e.g. `localStorage`) is vulnerable to cross-site scripting (XSS) attacks.
- **Decision:** Store JWT access tokens in `httpOnly`, `SameSite=Lax`, `Secure` cookies managed directly by FastAPI and the browser.
- **Rationale:** Prevents client-side scripts from accessing raw auth credentials. Meets enterprise security standards.

---

## ADR-006: Abstract Provider Boundary with Google Gemini Focus
- **Context:** While architecture requires decoupled interfaces (`BaseEmbeddingProvider`, `BaseLLMProvider`), the MVP standardizes strictly on Google Gemini as the sole external AI provider, backed by a deterministic Mock provider for local offline tests and CI/CD without API keys.
- **Decision:** Implement dedicated Gemini adapters (`GeminiEmbeddingProvider` and `GeminiLLMProvider`) and deterministic mock implementations. No second external provider is enabled for MVP.
- **Rationale:** Keeps ingestion, retrieval, and routes completely decoupled while focusing development and evaluation entirely on the Gemini API ecosystem.

---

## ADR-007: pgvector Dimensionality Standardized to 768 for Gemini
- **Context:** Gemini's `text-embedding-004` natively outputs 768 dimensions, and newer `gemini-embedding-*` models support 768-dimension Matryoshka output. pgvector's HNSW index performance scales inversely with dimension count.
- **Decision:** Define `document_chunks.embedding` as `vector(768)` in PostgreSQL.
- **Rationale:** 
  1. Guarantees 100% native compatibility with Google Gemini embeddings without custom pooling.
  2. Substantially reduces vector storage consumption and memory footprint compared to 1536 or 3072 dimensions.
  3. Accelerates Cosine distance search latency within pgvector while preserving semantic fidelity.
