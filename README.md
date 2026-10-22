# Mnemos — AI Knowledge Assistant

> **Your knowledge. Searchable. Understandable. Verifiable.**

Mnemos is an enterprise AI knowledge assistant engineered with strict Retrieval-Augmented Generation (RAG), semantic vector search, and verifiable citations.

Unlike generic conversational bots that hallucinate facts or invent references, Mnemos anchors every response to retrieved passages from uploaded documents (PDF, DOCX, TXT) and presents exact page numbers, similarity scores, and passage highlights. When evidence in the user's uploaded documents is insufficient, the system transparently reports that fact.

---

## Key Features

- **Multi-Format Ingestion**: Streaming upload and extraction of PDF (with 1-indexed page preservation via PyMuPDF), DOCX (via python-docx), and TXT files.
- **Multi-Tenant Workspace Isolation**: Every document, chunk, vector embedding, collection, and conversation thread is strictly partitioned by workspace. Cross-workspace access is physically denied by SQL predicates.
- **Provider-Independent AI Architecture**: Pluggable embedding providers (OpenAI `text-embedding-3-small`, Google Gemini `text-embedding-004`, deterministic word-hash Mock) and LLM providers (OpenAI `gpt-4o-mini`, Gemini `gemini-1.5-flash`, Mock).
- **Verifiable Citations**: Server-side citation validator parses `[citation:N]` tokens, validates passage overlap against the active workspace, and strips fabricated citations.
- **Slide-out Source Drawer**: Interactive inspection of original document metadata, vector cosine similarity gauges, and source excerpts.
- **Anti-Hallucination Guardrails**: Automatic insufficient-evidence fallback when retrieved chunks do not meet confidence thresholds.

---

## Architecture

```
                          ┌─────────────────────────────────────┐
                          │     Next.js 14 Frontend Client      │
                          │   (Tailwind CSS, Lucide, Dark UI)   │
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

- **Frontend (`apps/web`):** Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons.
- **Backend (`apps/api`):** Python 3.12, FastAPI, SQLAlchemy 2.x async, Alembic migrations, PyMuPDF, python-docx.
- **Database & Vectors:** PostgreSQL 16 with `pgvector` extension (Cosine distance `<=>` operator).
- **Security:** bcrypt password hashing (12 rounds), `httpOnly` secure JWT cookies, multi-tenant workspace isolation.

---

## Quickstart (Local Development)

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local backend development)
- Node.js 20+ (for local frontend development)

### 2. Running Full Stack with Docker Compose
```bash
docker-compose up --build
```
- **Web UI:** [http://localhost:3000](http://localhost:3000)
- **API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 3. Local Development (Without Docker)

#### Backend (`apps/api`)
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Run test suite:
```bash
python -m pytest -v
```

#### Frontend (`apps/web`)
```bash
cd apps/web
npm install
npm run dev
```

Run production build:
```bash
npm run build
```

---

## Environment Variables

### Backend (`apps/api/.env`)
| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `JWT_SECRET` | `dev_secret...` | HMAC secret for session JWT signing |
| `STORAGE_BACKEND` | `local` | File storage adapter (`local` or `s3`) |
| `STORAGE_LOCAL_ROOT` | `./data/storage` | Local directory for uploaded files |
| `EMBEDDING_PROVIDER` | `gemini` | Provider: `gemini` or `mock` |
| `GEMINI_EMBEDDING_MODEL` | `text-embedding-004` | Gemini embedding model (768 dimensions) |
| `EMBEDDING_DIMENSION` | `768` | Vector dimension matching `vector(768)` in pgvector |
| `LLM_PROVIDER` | `gemini` | Generation provider: `gemini` or `mock` |
| `GEMINI_CHAT_MODEL` | `gemini-1.5-flash` | Gemini chat/generation model |
| `GEMINI_API_KEY` | `""` | Google Gemini API Key from Google AI Studio |
| `RAG_SIMILARITY_THRESHOLD` | `0.70` | Minimum cosine similarity for RAG retrieval |
| `RAG_TOP_K` | `5` | Maximum number of chunks passed to LLM |

### Frontend (`apps/web/.env.local`)
| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | URL of the FastAPI backend |

---

## Verification & Test Evidence

- **Backend Pytest Suite:** 28/28 tests passing across Authentication, Workspace Isolation, PyMuPDF Ingestion, Vector Search, Single Document Scoping, Grounded RAG, Security Headers, and E2E Lifecycle.
- **Frontend Build:** Next.js production build completes with 0 errors and zero lint warnings.

---

## Specification Documents
Comprehensive design and architecture specifications are located in [`docs/`](./docs/):
- [Product Requirements Document (`PRD.md`)](./docs/PRD.md)
- [Software Requirements Specification (`SRS.md`)](./docs/SRS.md)
- [System Architecture (`ARCHITECTURE.md`)](./docs/ARCHITECTURE.md)
- [Database Design & pgvector Schema (`DATABASE_DESIGN.md`)](./docs/DATABASE_DESIGN.md)
- [API Specification (`API_SPECIFICATION.md`)](./docs/API_SPECIFICATION.md)
- [UI/UX Specification (`UI_UX_SPECIFICATION.md`)](./docs/UI_UX_SPECIFICATION.md)
- [Security & Privacy Guide (`SECURITY.md`)](./docs/SECURITY.md)
- [Test Plan & Evaluation Benchmark (`TEST_PLAN.md`)](./docs/TEST_PLAN.md)
- [Deployment Guide (`DEPLOYMENT.md`)](./docs/DEPLOYMENT.md)
- [Architecture Decision Records (`DECISIONS.md`)](./docs/DECISIONS.md)
- [Implementation Roadmap (`IMPLEMENTATION_PLAN.md`)](./docs/IMPLEMENTATION_PLAN.md)
