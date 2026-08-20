# Architecture — Waraq AI

This document provides a high-level overview of the Waraq AI architecture.

## The 5-Stage Pipeline

```
[PDF Upload]
    │  POST /api/upload-doc (multipart)
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 1: Parsing & Chunking        app/services/ingestion.py         │
│   pymupdf → per-page text + bbox blocks → page-safe chunks           │
│   Metadata: page_number, chunk_hash (dedup), bbox, doc_id            │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 2: Hybrid Indexing           app/services/indexing.py          │
│   Dense:  FastEmbed bge-small-en-v1.5 (384-d)                        │
│   Sparse: FastEmbed SPLADE (default)                                 │
│   → upsert to Qdrant collection "waraq_docs" (named vectors)      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 3: Hybrid Retrieval          app/services/retrieval.py         │
│   Dense query + sparse query → top-25 each → RRF fusion              │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 4: Reranking                 app/services/reranking.py         │
│   flashrank (ONNX) reranks 25 → top-5 context chunks                │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 5: Grounded Generation       app/services/generation.py        │
│   LiteLLM (BYOK: deepseek/gemini/openai/anthropic)                   │
│   strict system prompt → Markdown answer + page badges               │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
[Client]  POST /api/query | GET /api/stream-query (SSE)
```

## Module Map

| Module | File(s) | Responsibility |
|---|---|---|
| App factory | `app/main.py` | FastAPI app, CORS, lifespan, `/health` |
| Config | `app/core/config.py` | Pydantic-settings, `WARAQAI_` env prefix, BYOK LLM |
| Logging | `app/core/logging.py` | structlog JSON output |
| Vector store | `app/core/qdrant.py` | AsyncQdrantClient singleton, ping, collection mgmt |
| Schemas | `app/models/` | Pydantic v2 API + domain models |
| Services | `app/services/` | ingestion, indexing, retrieval, reranking, generation |
| Routers | `app/api/routes/` | `/upload-doc`, `/query`, `/stream-query` |
| Tests | `tests/` | pytest + TestClient |

## Locked Technical Decisions

| Decision | Choice | Why (vs naive alternative) |
|---|---|---|
| PDF parser | **pymupdf** | Only pymupdf gives exact per-page bounding-box coordinates via `page.get_text("dict")`. Stage 5 citations need real coords — pypdf's text extraction isn't layout-aware and can't give bbox. |
| Dense embeddings | **FastEmbed `BAAI/bge-small-en-v1.5`** (384-d) | Local, offline, zero API keys, no data leaves the machine. Strong recall/size trade-off for CPU. |
| Sparse embeddings | **FastEmbed SPLADE** | Same local runtime as dense; gives real lexical overlap signal (rare terms) that dense vectors miss. |
| Fusion | **Reciprocal Rank Fusion (RRF)** | Rank-based, no score calibration needed between two different similarity spaces (cosine vs BM25/SPLADE). K=60 standard. |
| Reranker | **flashrank (default)** | ONNX, no torch dependency, fast CPU inference, tiny memory. Keeps base install bloat-free. Optional extra: `sentence-transformers` + `cross-encoder/ms-marco-MiniLM-L-6-v2`. |
| LLM access | **LiteLLM, BYOK** | One client, provider-prefixed model strings (`deepseek/deepseek-chat`, `gemini/...`). Users bring their own key via `.env`; provider swap = env change, zero code change. |
| Qdrant access | **`AsyncQdrantClient`** | Async client keeps FastAPI's event loop free — no thread-pool blocking on vector I/O. |
| Chunking | Page-boundary-safe, size 800 / overlap 150 | Never split a chunk across pages → every chunk maps to exactly one page number → deterministic citations. Overlap preserves context across cut boundaries. |
| Collection layout | Named vectors `dense` + `sparse` in one collection | One Qdrant collection, two vector spaces, queried in parallel — no duplicate indexing, atomic per-doc cleanup. |

## API Contract

The frozen interface lives in `docs/api-contract.md`. The frontend and the backend both build against it.


