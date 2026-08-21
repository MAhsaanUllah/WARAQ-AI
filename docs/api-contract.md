# API Contract — Waraq AI

**Status: FROZEN for development.** This file is the interface the frontend and backend build against.

- Base URL: `http://localhost:8000` (dev)
- All request/response bodies are JSON (except multipart upload)
- SSE stream is `text/event-stream` with `data:` payloads
- Errors follow `{"detail": "..."}` (FastAPI default shape)

---

## 1. Health

### `GET /health`
**Purpose:** liveness + readiness (reports Qdrant connectivity).

```json
200 OK
{
  "status": "ok",
  "version": "0.1.0",
  "qdrant": "connected"
}
```
`qdrant` is `"connected"` or `"unavailable"`; `status` stays `"ok"` while the app itself is alive.

---

## 2. Document Upload

### `POST /api/upload-doc`
**Purpose:** ingest a PDF into the index.
**Content-Type:** `multipart/form-data`
**Body field:** `file` (PDF binary)

```json
201 Created
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "attention-is-all-you-need.pdf",
  "pages": 15,
  "chunks": 42,
  "status": "indexed"
}
```

**Behavior:**
- Parses + chunks the PDF (Stage 1), embeds + upserts (Stage 2), all async.
- Returns immediately only after indexing completes (201). For large files this may take seconds — the frontend should show a progress state.
- Idempotency: same document content → same `chunk_hash` set → re-upload overwrites, does not duplicate.
- **Quota Limits Enforced:** Maximum 5 documents per user. 5 MB max file size. 50 pages max per PDF.

**Errors:**
- `400` — not a PDF / unreadable file / extraction limit exceeded (>50 pages)
- `403` — Portfolio limit reached (max 5 documents)
- `413` — file too large (limit: 5 MB)
- `503` — Qdrant unavailable

### `POST /api/upload-docs`
**Purpose:** ingest MULTIPLE PDFs in one request (batch).
**Content-Type:** `multipart/form-data`
**Body field:** `files` (repeated, PDF binaries)

```json
201 Created
{
  "results": [
    {"document_id": "uuid", "filename": "a.pdf", "pages": 3, "chunks": 8, "status": "indexed"},
    {"document_id": "uuid", "filename": "b.pdf", "pages": 5, "chunks": 12, "status": "indexed"}
  ],
  "total_pages": 8,
  "total_chunks": 20
}
```

---

## 2b. Document Listing (Resources)

### `GET /api/documents`
**Purpose:** list every indexed document so the UI can build the "Select Resources" dialog (Notebook-style scoped chat).

```json
200 OK
[
  {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "attention-is-all-you-need.pdf",
    "pages": 15,
    "chunks": 42,
    "status": "indexed"
  }
]
```

**Errors:** `503` — Qdrant unavailable.

---

## 3. Query (non-streaming)

### `POST /api/query`
**Purpose:** single-shot RAG answer.

```json
// Request
{
  "question": "What is multi-head attention?",
  "top_k_candidates": 25,
  "top_k_final": 5,
  "document_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```
`top_k_candidates` / `top_k_final` optional, default to settings (25 / 5).
`document_ids` optional: restrict retrieval to these documents (Notebook/Resources scoped chat). Omitted or empty = global search over all indexed files.

```json
// Response 200 OK
{
  "answer": "Multi-head attention runs **h** attention heads...",
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "attention-is-all-you-need.pdf",
      "page": 3,
      "chunk_hash": "a1b2c3...",
      "bbox": {"x0": 72.0, "y0": 486.0, "x1": 522.0, "y1": 540.0},
      "score": 0.93,
      "snippet": "we employ h = 8 parallel attention heads..."
    }
  ],
  "processing_ms": 842
}
```

**Behavior:**
- Runs Stages 3–5: hybrid retrieval → rerank → grounded generation.
- `sources[]` is the citation contract — **every** claim in `answer` must trace to a source here.
- `bbox` is optional `null` when coordinates are unavailable; `page` is always present.
- `sources[]` sorted by `score` descending; **this is the citation order** the LLM must reference (`[1]`, `[2]`, ...).

**Errors:**
- `422` — empty question / bad enum
- `503` — Qdrant unavailable

---

## 4. Streaming Query (SSE)

### `GET /api/stream-query`
**Purpose:** stream the same pipeline as `/api/query`, but the answer arrives token-by-token.
**Query params:** 
- `question=...`
- `top_k_candidates=25`
- `top_k_final=5`
- `document_ids=uuid1,uuid2`
- `use_web_search=false`
- `llm_provider=deepseek` (Stateless BYOK)
- `llm_api_key=sk-123...` (Stateless BYOK)
- `search_provider=tavily` (Stateless BYOK)
- `search_api_key=tvly-123...` (Stateless BYOK)

`document_ids` is a comma-separated list of document UUIDs; omitting it = global search.

**Event flow:**

```
event: status
data: {"stage": "retrieving", "message": "Fused 25 candidates via RRF"}

event: status
data: {"stage": "reranking", "message": "Selected top 5 chunks"}

event: answer_delta
data: {"delta": "Multi-head attention"}

event: answer_delta
data: {"delta": " runs **h** heads..."}

event: done
data: {"sources": [...same schema as /api/query...], "processing_ms": 900}
```

**Event types:**
| event | payload |
|---|---|
| `status` | `{"stage": "retrieving"\|"reranking"\|"generating", "message": str}` |
| `answer_delta` | `{"delta": str}` — append to answer buffer |
| `done` | `{"sources": Source[], "processing_ms": int}` |
| `error` | `{"detail": str}` — stream ends after this |

**Contract invariants (frontend must rely on):**
1. `answer_delta` events arrive **after** the `status: generating` event.
2. `done` is always the **last** event on success — it carries the final `sources[]`.
3. If an `error` event arrives, there is no `done` event; render the error and stop.

---

## 5. Source Schema (shared by both query endpoints)

```json
{
  "document_id": "string (uuid)",
  "filename": "string",
  "page": "int >= 1",
  "chunk_hash": "string (sha256 hex)",
  "bbox": {"x0": "float", "y0": "float", "x1": "float", "y1": "float"} | null,
  "score": "float 0..1",
  "snippet": "string"
}
```

**Invariants:**
- `page` is the **real PDF page number** (1-indexed), never a hallucinated one.
- `sources` is non-empty on every successful answer; empty `sources` ⇒ server error, not an answer.
- `snippet` is the exact text of the chunk used (trimmed), so the frontend can render expandable citation cards.

---

## 6. CORS

- Allowed origin: `http://localhost:5173` (Vite dev server) — configurable via `WARAQAI_CORS_ORIGINS`.
- Methods: `GET, POST, OPTIONS`. Headers: `Content-Type`.

---

## 7. OpenAPI

Interactive docs auto-generated at `/docs` (Swagger UI) and `/openapi.json`. The frontend should **not** depend on these at runtime — the schemas above are the contract.
