

"""RAG API routes: upload, query, stream, documents, settings."""

from __future__ import annotations

import json
import time
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.core.auth import CurrentUser
from app.core.config import get_settings
from app.core.qdrant import ping_qdrant
from app.models.api import (
    AnswerResponse,
    BatchUploadResponse,
    DocumentInfo,
    LLMSettings,
    LLMSettingsOut,
    SearchSettings,
    Source,
    UploadResponse,
)
from app.models.retrieval import QueryRequest, RerankedResult
from app.services.documents import list_documents
from app.services.extraction import ExtractionError
from app.services.generation import (
    LLMNotConfiguredError,
    generate_answer,
    stream_answer,
    to_source,
)
from app.services.ingestion import ingest_document
from app.services.reranking import rerank
from app.services.retrieval import hybrid_search
from app.services.websearch import search_configured, web_search

router = APIRouter(prefix="/api", tags=["rag"])

async def _require_qdrant() -> None:
    """Fail fast with 503 if the vector store is unreachable."""
    if not await ping_qdrant():
        raise HTTPException(status_code=503, detail="Qdrant unavailable")


async def _retrieve_and_rerank(request: QueryRequest, user_id: str) -> list[RerankedResult]:
    """Shared Stages 3-4: hybrid search then rerank. Returns top chunks."""
    settings = get_settings()
    top_final = request.top_k_final or settings.top_k_final

    candidates = await hybrid_search(request, user_id)
    if not candidates:
        raise HTTPException(status_code=404, detail="No documents indexed yet")

    return await rerank(request.question, candidates, top_k=top_final)




@router.get("/documents", response_model=list[DocumentInfo])
async def get_documents(user_id: CurrentUser) -> list[DocumentInfo]:
    """List the current user's indexed documents."""
    await _require_qdrant()
    return await list_documents(user_id)

@router.post("/upload-doc", response_model=UploadResponse, status_code=201)
async def upload_doc(
    user_id: CurrentUser,
    file: Annotated[UploadFile, File(...)],
) -> UploadResponse:
    """Ingest a PDF: parse, chunk, embed, upsert (all async)."""
    await _require_qdrant()

    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_mb} MB limit",
        )

    try:
        result = await ingest_document(data, file.filename or "document.pdf", user_id)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadResponse(
        document_id=result.document_id,
        filename=result.filename,
        pages=result.pages,
        chunks=result.chunks,
        status=result.status,
    )

@router.post("/upload-docs", response_model=BatchUploadResponse, status_code=201)
async def upload_docs(
    user_id: CurrentUser,
    files: Annotated[list[UploadFile], File(...)],
) -> BatchUploadResponse:
    """Ingest multiple PDFs in one request. Returns per-file results."""
    await _require_qdrant()

    existing_docs = await list_documents(user_id)
    if len(existing_docs) + len(files) > 5:
        raise HTTPException(
            status_code=403, 
            detail="Portfolio limit: Maximum 5 documents allowed per user."
        )

    settings = get_settings()
    max_bytes = 5 * 1024 * 1024  # Portfolio limit: 5MB
    results: list[UploadResponse] = []

    for file in files:
        data = await file.read()
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} exceeds 5 MB limit",
            )
        try:
            result = await ingest_document(data, file.filename or "document.pdf", user_id)
        except ExtractionError as exc:
            raise HTTPException(status_code=400, detail=f"{file.filename}: {exc}") from exc
        results.append(
            UploadResponse(
                document_id=result.document_id,
                filename=result.filename,
                pages=result.pages,
                chunks=result.chunks,
                status=result.status,
            )
        )

    return BatchUploadResponse(
        results=results,
        total_pages=sum(r.pages for r in results),
        total_chunks=sum(r.chunks for r in results),
    )

@router.post("/query", response_model=AnswerResponse)
async def query_doc(request: QueryRequest, user_id: CurrentUser) -> AnswerResponse:
    """Stages 3-5: hybrid search, rerank, grounded answer + citations."""
    await _require_qdrant()

    start = time.perf_counter()
    chunks = await _retrieve_and_rerank(request, user_id)

    web_context = None
    if request.use_web_search:
        if not search_configured():
            raise HTTPException(
                status_code=503,
                detail="Web search is enabled but no search API key is set. "
                       "Add a Tavily or Brave key in the Settings page.",
            )
        web_context = await web_search(request.question)

    try:
        answer = await generate_answer(request.question, chunks, web_context)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sources = [to_source(c) for c in chunks]

    return AnswerResponse(
        answer=answer,
        sources=sources,
        processing_ms=int((time.perf_counter() - start) * 1000),
    )

@router.get("/stream-query")
async def stream_query(
    user_id: CurrentUser,
    question: str = Query(min_length=1, max_length=2000),
    top_k_candidates: int | None = Query(default=None, ge=1, le=100),
    top_k_final: int | None = Query(default=None, ge=1, le=20),
    use_web_search: bool = Query(default=False),
    document_ids: str | None = Query(default=None, description="Comma-separated document UUIDs"),
    llm_provider: str | None = Query(default=None),
    llm_api_key: str | None = Query(default=None),
    search_provider: str | None = Query(default=None),
    search_api_key: str | None = Query(default=None),
):
    """SSE: status events → answer_delta* → done{sources, processing_ms}."""
    await _require_qdrant()
    parsed_ids = [d.strip() for d in document_ids.split(",") if d.strip()] if document_ids else None
    request = QueryRequest(
        question=question,
        top_k_candidates=top_k_candidates,
        top_k_final=top_k_final,
        use_web_search=use_web_search,
        document_ids=parsed_ids,
    )

    start = time.perf_counter()
    settings = get_settings()
    top_final = request.top_k_final or settings.top_k_final

    async def event_stream():
        try:
            yield _sse("status", {"stage": "retrieving", "message": "Fused candidates via RRF"})
            candidates = await hybrid_search(request, user_id)
            if not candidates:
                yield _sse("error", {"detail": "No documents indexed yet"})
                return

            yield _sse("status", {"stage": "reranking", "message": f"Selected top {top_final} chunks"})
            chunks = await rerank(request.question, candidates, top_k=top_final)

            web_context = None
            if request.use_web_search:
                yield _sse("status", {"stage": "searching", "message": "Fetching web results"})
                if not search_configured(search_api_key):
                    yield _sse(
                        "error",
                        {
                            "detail": "Web search is enabled but no search API key is set."
                        },
                    )
                    return
                web_context = await web_search(request.question, provider=search_provider, api_key=search_api_key)

            yield _sse("status", {"stage": "generating", "message": "Synthesizing answer"})
            try:
                async for delta in stream_answer(request.question, chunks, web_context, llm_provider, llm_api_key):
                    yield _sse("answer_delta", {"delta": delta})
            except LLMNotConfiguredError as exc:
                yield _sse("error", {"detail": str(exc)})
                return

            sources = [to_source(c) for c in chunks]
            yield _sse(
                "done",
                {"sources": [s.model_dump() for s in sources],
                 "processing_ms": int((time.perf_counter() - start) * 1000)},
            )
        except Exception as exc:
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(event: str, data: dict) -> str:
    """Serialize one SSE frame: `event: <name>\ndata: <json>\n\n`."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
