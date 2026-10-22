# API Specification — Mnemos

**Base URL:** `/api/v1`  
**Protocol:** HTTPS / JSON  
**Authentication:** Bearer Token via `httpOnly` cookie (`access_token`)  
**Related Documents:** [ARCHITECTURE.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/ARCHITECTURE.md), [SECURITY.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/SECURITY.md)

---

## 1. Global Response & Error Standards

### Success Envelope
Endpoints returning single entities or paginated sets follow a standard response structure:
```json
{
  "success": true,
  "data": { ... },
  "metadata": { ... } // optional pagination or query telemetry
}
```

### Error Envelope
No raw Python exceptions or stack traces are ever exposed to the client:
```json
{
  "success": false,
  "error": {
    "code": "DOCUMENT_EXTRACTION_FAILED",
    "message": "The uploaded PDF appears password protected or unreadable.",
    "details": null
  }
}
```

---

## 2. Core Endpoints

### 2.1 Health & Readiness
- **`GET /health`**
  - **Description:** Basic liveness probe.
  - **Response 200:** `{"status": "ok", "timestamp": "2026-10-19T14:45:00Z"}`
- **`GET /ready`**
  - **Description:** Validates connectivity to PostgreSQL database and pgvector extension.
  - **Response 200:** `{"status": "ready", "database": "connected", "pgvector": "available"}`

### 2.2 Authentication & Workspace (`/auth`)
- **`POST /auth/register`**
  - **Body:** `{"email": "user@example.com", "password": "...", "full_name": "..."}`
  - **Response 201:** `{"success": true, "data": {"user_id": "...", "workspace_id": "..."}}` (Sets `access_token` cookie)
- **`POST /auth/login`**
  - **Body:** `{"email": "user@example.com", "password": "..."}`
  - **Response 200:** `{"success": true, "data": {"user_id": "...", "workspace_id": "..."}}`
- **`POST /auth/logout`**
  - **Response 200:** `{"success": true, "data": {"message": "Logged out"}}` (Clears auth cookie)
- **`GET /auth/me`**
  - **Response 200:** User profile and current workspace details.

### 2.3 Documents (`/documents`)
- **`POST /documents`**
  - **Description:** Uploads a document file (`multipart/form-data`).
  - **Payload:** `file: UploadFile`, `collection_ids?: UUID[]`
  - **Response 202 Accepted:**
    ```json
    {
      "success": true,
      "data": {
        "id": "c1f7a28e-...",
        "filename": "Q3_Financials.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1048576,
        "status": "PENDING",
        "job_id": "d2e8b39f-..."
      }
    }
    ```
- **`GET /documents`**
  - **Query Params:** `page=1&limit=20&collection_id=...&search=...`
  - **Response 200:** List of documents in workspace with status, page counts, and sizes.
- **`GET /documents/{id}`**
  - **Response 200:** Complete document metadata, status, collections, and parsed chunk count.
- **`GET /documents/{id}/status`**
  - **Response 200:** `{"status": "INDEXED", "page_count": 14, "chunk_count": 42, "error": null}`
- **`GET /documents/{id}/content`**
  - **Query Params:** `page_number=14`
  - **Response 200:** Text content for inspection preview.
- **`DELETE /documents/{id}`**
  - **Description:** Hard-deletes document, associated chunks, vectors, citations, and storage file.
  - **Response 200:** `{"success": true, "data": {"deleted": true}}`

### 2.4 Collections (`/collections`)
- **`GET /collections`**: Lists workspace collections with document counts.
- **`POST /collections`**: Creates collection `{ "name": "...", "description": "..." }`.
- **`PATCH /collections/{id}`**: Renames or updates description.
- **`DELETE /collections/{id}`**: Deletes collection (preserves constituent documents).
- **`POST /collections/{id}/documents`**: Assigns documents to collection `{ "document_ids": [...] }`.
- **`DELETE /collections/{id}/documents/{document_id}`**: Removes document from collection.

### 2.5 Conversations & Chat Query (`/chat`)
- **`GET /chat/conversations`**: Lists conversations in the active workspace.
- **`POST /chat/conversations`**: Creates a new thread `{ "title": "..." }`.
- **`GET /chat/conversations/{id}`**: Returns messages, roles, and citation records.
- **`DELETE /chat/conversations/{id}`**: Deletes conversation.
- **`POST /chat/query`**
  - **Payload:**
    ```json
    {
      "question": "What drove the operating cost increases in Q3?",
      "conversation_id": "optional-uuid",
      "scope": "ALL", // or "COLLECTION"
      "scope_id": null // or collection UUID
    }
    ```
  - **Response 200:**
    ```json
    {
      "success": true,
      "data": {
        "conversation_id": "6a9e1d84-...",
        "message_id": "7b0f2e95-...",
        "answer": "Operating costs in Q3 increased primarily due to cloud infrastructure expansion [1] and new R&D personnel hiring [2].",
        "insufficient_evidence": false,
        "citations": [
          {
            "id": "citation-uuid-1",
            "citation_index": 1,
            "document_id": "doc-uuid-a",
            "document_title": "Q3_Financial_Report.pdf",
            "page_number": 14,
            "excerpt": "Cloud infrastructure spending increased by 28% year-over-year to support expanded analytics workloads.",
            "chunk_id": "chunk-uuid-1",
            "similarity_score": 0.94
          },
          {
            "id": "citation-uuid-2",
            "citation_index": 2,
            "document_id": "doc-uuid-b",
            "document_title": "R&D_Budget_Proposal.docx",
            "page_number": null,
            "excerpt": "Headcount in the core engineering and R&D division expanded by 15 full-time engineers.",
            "chunk_id": "chunk-uuid-2",
            "similarity_score": 0.89
          }
        ],
        "usage": {
          "prompt_tokens": 820,
          "completion_tokens": 140
        }
      }
    }
    ```
