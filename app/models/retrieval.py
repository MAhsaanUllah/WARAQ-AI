"""Retrieval domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.ingestion import BBox


class QueryRequest(BaseModel):
    """A RAG query with optional retrieval knobs."""

    question: str = Field(min_length=1, max_length=2000)
    top_k_candidates: int | None = Field(default=None, ge=1, le=100)
    top_k_final: int | None = Field(default=None, ge=1, le=20)
    use_web_search: bool = False
    document_ids: list[str] | None = Field(
        default=None,
        description="Restrict retrieval to these document_ids (empty/None = global search)",
    )


class RetrievedChunk(BaseModel):
    """A single chunk returned by Qdrant hybrid search (pre-rerank)."""

    chunk_id: str
    doc_id: str
    filename: str
    page_number: int = Field(ge=1)
    text: str
    bbox: BBox | None = None
    score: float | None = None


class RerankedResult(BaseModel):
    """A reranked chunk, ready for context injection + citation."""

    chunk_id: str
    doc_id: str
    filename: str
    page_number: int = Field(ge=1)
    text: str
    bbox: BBox | None = None
    score: float = Field(ge=0, le=1)
    rank: int = Field(ge=1)
