# Product Requirements Document (PRD) — Mnemos

**Product Name:** Mnemos  
**Tagline:** *Your knowledge. Searchable. Understandable. Verifiable.*  
**Target Release:** MVP v1.0  
**Document Status:** Approved Baseline  

---

## 1. Product Vision & Differentiator

Mnemos is an enterprise-grade AI knowledge assistant designed for knowledge workers, researchers, legal analysts, and technical teams who need trustworthy answers derived from their own document corpus.

Unlike generic conversational chatbots that synthesize answers without attribution or hallucinate plausible details, **Mnemos is grounded strictly in retrieved passages with verifiable, clickable citations** (document name, page number for paginated formats, exact text excerpts, and vector similarity context). When evidence in the user's uploaded documents is insufficient, ambiguous, or conflicting, the system explicitly reports that fact rather than fabricating answers.

---

## 2. Core Personas & Use Cases

### Personas
1. **Research & Intelligence Analyst:** Uploads dense technical reports, scientific whitepapers, and market assessments. Needs cross-document question answering with exact page citations to paste into briefings.
2. **Legal & Compliance Auditor:** Audits multi-page contracts, bylaws, and regulatory guidelines. Needs verifiable quotes and guarantees that private documents are strictly isolated per workspace.
3. **Product & Engineering Lead:** Ingests API specs, system architecture guides, and internal post-mortems to rapidly onboard team members and resolve architectural queries.

### Key Workflows
- **Multi-Format Ingestion:** Drag-and-drop or select PDF, DOCX, and TXT files. System streams file chunks, inspects MIME/magic signatures, extracts raw text with page demarcation, chunks text, generates vector embeddings, and provides live status updates.
- **Collection Organization:** Group related documents into topic collections (e.g., "Q3 Financials", "Security Policies").
- **Scoped Semantic Search & Chat:** Ask questions targeting all workspace documents or a specific collection.
- **Source Inspection & Verification:** Click inline citation pills (`[1]`, `[2]`) to open a dedicated Source Inspection Panel displaying the exact page, chunk similarity score, and passage highlight.
- **Insufficient Evidence Handling:** When semantic similarity thresholds or retrieved contexts fail to support an answer, the model responds with a structured, standard insufficient-evidence state.

---

## 3. Scope & Feature Boundaries

### In Scope (MVP)
- **Document Formats:** PDF (preserving page numbers via PyMuPDF), DOCX (via python-docx), TXT (UTF-8 plain text).
- **User-Level Authorization:** Single-user data isolation for MVP; every query, document, chunk, and conversation is partitioned by user/workspace ownership.
- **Dedicated AI Provider:** Google Gemini API exclusively (`GEMINI_CHAT_MODEL`, `GEMINI_EMBEDDING_MODEL` e.g., `text-embedding-004` / `gemini-embedding-*` at 768 dimensions), wrapped in a decoupled provider adapter.
- **Ingestion Pipeline:** Non-blocking background ingestion with status tracking (`PENDING`, `PARSING`, `CHUNKING`, `EMBEDDING`, `INDEXED`, `FAILED`).
- **Semantic Retrieval & RAG:** Vector search powered by pgvector (Cosine distance `vector(768)`), grounded prompting with anti-hallucination defenses.
- **Verifiable Citations:** Citation schema linking message responses directly to chunk IDs, document IDs, page numbers, and exact excerpts.
- **Frontend Experience:** Next.js single-page application built on Tailwind and Lucide, featuring dark-canvas command center (Knowledge Dashboard + AI Chat Workspace with Source Drawer). Scope selector offers **"all documents"** or **"single document"** only.

### Out of Scope (Post-MVP / Release 2)
- Multi-role workspaces and team collaboration permissions (RBAC).
- Topic Collections and collection selectors (out of scope for MVP; reserved for Release 2).
- Distributed queue (Celery/Redis); FastAPI `BackgroundTasks` is utilized for MVP.
- Multiple LLM providers (MVP standardizes exclusively on Google Gemini).
- Advanced analytics, admin dashboards, reranking, and billing systems.

---

## 4. Key Performance & Quality Metrics

1. **Groundedness:** 0% invented citations. Every citation must map to a retrieved database chunk with verified workspace ownership.
2. **Ingestion Latency:** Under 5 seconds for documents under 20 pages (excluding external embedding API network latency).
3. **Retrieval Latency:** Sub-200ms for vector search over 10,000 chunks using indexed pgvector.
4. **UI Responsiveness:** Sub-100ms UI interactions; clear skeleton loaders and progress bars during streaming and background jobs.
