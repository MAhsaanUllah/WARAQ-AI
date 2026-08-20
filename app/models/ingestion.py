"""Ingestion domain models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class BBox(BaseModel):
    """Bounding-box coordinates in PDF points."""

    x0: float
    y0: float
    x1: float
    y1: float


class Page(BaseModel):
    """One extracted PDF page: text + per-line bounding boxes."""

    page_number: int = Field(ge=1, description="1-indexed PDF page number")
    text: str
    bboxes: list[BBox] = Field(default_factory=list)


class Chunk(BaseModel):
    """A page-boundary-safe chunk ready for embedding."""

    chunk_id: str = Field(description="Deterministic UUIDv5 of the chunk text (Qdrant point ID)")
    doc_id: str
    filename: str
    page_number: int = Field(ge=1)
    text: str
    chunk_index: int = Field(ge=0, description="Order within the document")
    bbox: BBox | None = None

    @property
    def char_count(self) -> int:
        return len(self.text)


class Document(BaseModel):
    """A parsed PDF document, prior to chunking."""

    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    pages: list[Page]
    chunks: list[Chunk] = Field(default_factory=list)


class IngestResult(BaseModel):
    """Outcome of ingesting one document."""

    document_id: str
    filename: str
    pages: int
    chunks: int
    status: str = "indexed"
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
