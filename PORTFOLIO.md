# Mnemos — AI Knowledge Assistant: Portfolio & Executive Architecture Summary

> **Your knowledge. Searchable. Understandable. Verifiable.**

**Mnemos** is a production-grade, enterprise AI knowledge assistant built inside Google Antigravity IDE and integrated with Google Stitch. It differentiates itself from generic conversational chatbots by guaranteeing evidence-grounded answers anchored in user-uploaded documents (PDF, DOCX, TXT), emitting verifiable page-level citations, and honestly refusing to speculate when source evidence is insufficient.

---

## 1. System Architecture & Component Mapping

```
                                      ┌─────────────────────────────────────┐
                                      │      Next.js 14 Web Frontend        │
                                      │  (Tailwind CSS, Dark Canvas Theme)  │
                                      └──────────────────┬──────────────────┘
                                                         │ HTTP / SSE
                                                         ▼
                                      ┌─────────────────────────────────────┐
                                      │        FastAPI Gateway Router       │
                                      │   (Auth, Documents, Search, Chat)   │
                                      └──────────┬───────────────┬──────────┘
                                                 │               │
                               ┌─────────────────┴────┐     ┌────┴─────────────────┐
                               │   PostgreSQL 16+     │     │    AI Model Layer    │
                               │   with pgvector      │     │  (Google Gemini API) │
                               │  (768-dim HNSW Index)│     └──────────────────────┘
                               └──────────────────────┘
```

### Core Subsystems:
1. **Frontend Client (`apps/web`)**: Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide Icons, bespoke tokens (`#0B0F19` canvas, `#111827` surface, Indigo/Blue accents), and responsive drawer panels.
2. **Backend API (`apps/api`)**: Python 3.12, FastAPI, SQLAlchemy 2.x async, Alembic migrations, PyMuPDF, python-docx, and Pydantic v2 validation.
3. **Storage Engine (`apps/api/app/storage`)**: Abstract `StorageAdapter` generating cryptographically safe UUID keys (`workspaces/{ws_id}/documents/{doc_uuid}.bin`), preventing path traversal.
4. **Validation & Extraction Subsystem (`apps/api/app/ingestion`)**:
   - Magic byte validation (`%PDF-`, `PK\x03\x04`), 50 MB size limit, streaming SHA-256 deduplication.
   - PyMuPDF 1-indexed page demarcation (`ExtractedPage`).
   - `RecursiveCharacterChunker` (500 tokens, 10% overlap, preserving paragraph/sentence boundaries).
5. **Provider-Agnostic Embeddings (`apps/api/app/embeddings`)**: Pluggable `BaseEmbeddingProvider` supporting OpenAI (`text-embedding-3-small`), Google Gemini (`text-embedding-004`), and deterministic word-hashed pseudo-embeddings for offline testing.
6. **Vector Search Engine (`apps/api/app/services/search.py`)**: Multi-tenant workspace scoped pgvector Cosine distance (`<=>`) queries with HNSW indexing and optional collection filtering.
7. **Grounded RAG & Citation Validation (`apps/api/app/rag`)**:
   - Strict anti-hallucination prompt guardrails (`GROUNDED_SYSTEM_PROMPT`).
   - Server-side `CitationValidator` checking passage overlap and stripping ungrounded citations.
   - Structured insufficient-evidence state reporting when evidence is missing.
8. **Security Subsystem**:
   - Argon2id/bcrypt password hashing (12 rounds).
   - `httpOnly`, `Secure`, `SameSite=Lax` JWT cookies.
   - HTTP security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`).

---

## 2. Milestone Execution Record (Milestones A – L)

| Milestone | Title | Status | Key Deliverable |
|---|---|---|---|
| **A** | Design & Inspection | **APPROVED** | Stitch design inspection (`projects/4570473511615439957`), visual mockups, and `milestone_a_design_specification.md`. |
| **B** | Architecture & Requirements | **APPROVED** | 11 comprehensive specification documents authored in `mnemos/docs/`. |
| **C** | Repository Foundation | **APPROVED** | Monorepo layout, Docker Compose, FastAPI foundation (`apps/api`), Next.js foundation (`apps/web`). |
| **D** | Database & Authentication | **APPROVED** | SQLAlchemy async schema, Alembic migration, `pgvector` Vector(768) columns, JWT auth with httpOnly cookies. |
| **E** | Document Ingestion Pipeline | **APPROVED** | PyMuPDF page-preserving extractor, python-docx, text extractor, recursive chunker, async background task pipeline. |
| **F** | Embeddings & Vector Search | **APPROVED** | Provider-independent embedding interface, vector generation in pipeline, pgvector cosine search with tenant isolation. |
| **G** | Grounded RAG & Citations | **APPROVED** | Anti-hallucination prompt, server-side citation validation, ungrounded citation stripping, honest refusal engine. |
| **H** | Frontend UI Components | **APPROVED** | High-fidelity dark-canvas UI matching Stitch: Sidebar, Knowledge Dashboard, Chat Workspace, and Source Drawer. |
| **I** | Integration & E2E Testing | **APPROVED** | 10-phase end-to-end user lifecycle test (`test_full_rag_lifecycle_e2e`) passing cleanly. |
| **J** | Performance & Hardening | **APPROVED** | HTTP security headers middleware, CORS audit, unauthenticated route protection, 26/26 backend tests passing. |
| **K** | Documentation & Deployment | **APPROVED** | Next.js standalone containerization, full docker-compose orchestration, and comprehensive root `README.md`. |
| **L** | Portfolio Packaging | **APPROVED** | Final portfolio walkthrough, executive summary, and project completion sign-off. |

---

## 3. Verified Test & Build Benchmarks

### Backend Test Suite (Pytest)
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\manoj\OneDrive\Desktop\Mnemos AI Knowledge Assitant\mnemos\apps\api
configfile: pyproject.toml
testpaths: app/tests
plugins: anyio-4.15.1, asyncio-1.4.0

app/tests/test_auth.py::test_register_success PASSED                     [  3%]
app/tests/test_auth.py::test_register_duplicate_email PASSED             [  7%]
app/tests/test_auth.py::test_login_success PASSED                        [ 11%]
app/tests/test_auth.py::test_login_invalid_password PASSED               [ 15%]
app/tests/test_auth.py::test_get_me_with_cookie PASSED                   [ 19%]
app/tests/test_e2e.py::test_full_rag_lifecycle_e2e PASSED                [ 23%]
app/tests/test_health.py::test_root_health PASSED                        [ 26%]
app/tests/test_health.py::test_api_v1_health PASSED                      [ 30%]
app/tests/test_health.py::test_api_v1_ready PASSED                       [ 34%]
app/tests/test_ingestion.py::test_upload_and_ingest_pdf PASSED           [ 38%]
app/tests/test_ingestion.py::test_upload_and_ingest_docx PASSED          [ 42%]
app/tests/test_ingestion.py::test_upload_and_ingest_txt PASSED           [ 46%]
app/tests/test_ingestion.py::test_reject_corrupted_magic_header PASSED   [ 50%]
app/tests/test_ingestion.py::test_reject_empty_file PASSED               [ 53%]
app/tests/test_ingestion.py::test_document_cross_workspace_isolation PASSED [ 57%]
app/tests/test_ingestion.py::test_delete_document_success PASSED         [ 61%]
app/tests/test_rag.py::test_grounded_conversation_with_citations PASSED  [ 65%]
app/tests/test_rag.py::test_insufficient_evidence_refusal PASSED         [ 69%]
app/tests/test_search.py::test_semantic_search_success PASSED            [ 73%]
app/tests/test_search.py::test_semantic_search_threshold_filtering PASSED [ 76%]
app/tests/test_search.py::test_search_workspace_tenant_isolation PASSED  [ 80%]
app/tests/test_security.py::test_security_headers_present PASSED         [ 84%]
app/tests/test_security.py::test_cors_policy PASSED                      [ 88%]
app/tests/test_security.py::test_unauthenticated_protected_endpoint PASSED [ 92%]
app/tests/test_workspace_isolation.py::test_workspace_isolation_denies_cross_workspace_access PASSED [ 96%]
app/tests/test_workspace_isolation.py::test_workspace_isolation_denies_nonexistent_workspace PASSED [100%]

======================= 26 passed, 2 warnings in 19.83s =======================
```

### Frontend Production Build (Next.js 14)
```
> mnemos-web@0.1.0 build
> next build

  ▲ Next.js 14.2.35
  - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
   Generating static pages (0/4) ...
   Generating static pages (1/4) 
   Generating static pages (2/4) 
   Generating static pages (3/4) 
 ✓ Generating static pages (4/4)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    9.39 kB        96.6 kB
└ ○ /_not-found                          873 B          88.1 kB
+ First Load JS shared by all            87.2 kB
  ├ chunks/117-dc300875ec913ee5.js       31.7 kB
  ├ chunks/fd9d1056-c96c49782430d626.js  53.6 kB
  └ other shared chunks (total)          1.86 kB

○  (Static)  prerendered as static content
```
