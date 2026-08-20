"""API-boundary schemas matching the frozen api-contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.ingestion import BBox


class Source(BaseModel):
    """One verifiable citation: real page number + bbox + snippet."""

    document_id: str
    filename: str
    page: int = Field(ge=1)
    chunk_hash: str
    bbox: BBox | None = None
    score: float = Field(ge=0, le=1)
    snippet: str


class UploadResponse(BaseModel):
    """POST /api/upload-doc → 201."""

    document_id: str
    filename: str
    pages: int
    chunks: int
    status: str


class BatchUploadResponse(BaseModel):
    """POST /api/upload-docs → 201. One entry per file."""

    results: list[UploadResponse]
    total_pages: int
    total_chunks: int


class DocumentInfo(BaseModel):
    """GET /api/documents → one entry per indexed file."""

    document_id: str
    filename: str
    pages: int
    chunks: int
    status: str = "indexed"


class AnswerResponse(BaseModel):
    """POST /api/query → 200."""

    answer: str
    sources: list[Source]
    processing_ms: int


class StatusEvent(BaseModel):
    """SSE `status` event."""

    stage: str
    message: str


class AnswerDeltaEvent(BaseModel):
    """SSE `answer_delta` event."""

    delta: str


class DoneEvent(BaseModel):
    """SSE `done` event — carries the final citations."""

    sources: list[Source]
    processing_ms: int


class ErrorEvent(BaseModel):
    """SSE `error` event."""

    detail: str


class LLMSettings(BaseModel):
    """Runtime BYOK LLM configuration."""

    provider: Literal["deepseek", "gemini", "openai", "anthropic", "openrouter"]
    api_key: str = Field(min_length=8)


class SearchSettings(BaseModel):
    """Runtime BYOK web-search configuration."""

    provider: Literal["tavily", "brave"]
    api_key: str = Field(min_length=8)


class LLMSettingsOut(BaseModel):
    """What GET /api/settings returns — never the key itself."""

    provider: str
    has_api_key: bool
    search_provider: str | None = None
    has_search_key: bool = False
