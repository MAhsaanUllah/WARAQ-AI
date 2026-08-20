"""Page-boundary-safe chunking with overlap."""

from __future__ import annotations

import hashlib
import uuid

from app.core.config import get_settings
from app.models.ingestion import BBox, Chunk, Document


def chunk_document(document: Document) -> list[Chunk]:
    """Chunk every page independently; never across page boundaries."""
    settings = get_settings()
    chunks: list[Chunk] = []

    for page in document.pages:
        page_chunks = _chunk_page(
            page_number=page.page_number,
            text=page.text,
            bboxes=page.bboxes,
            filename=document.filename,
            doc_id=document.doc_id,
            size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        chunks.extend(page_chunks)

    for index, chunk in enumerate(chunks):
        chunk.chunk_index = index

    return chunks


def _chunk_page(
    *,
    page_number: int,
    text: str,
    bboxes: list[BBox],
    filename: str,
    doc_id: str,
    size: int,
    overlap: int,
) -> list[Chunk]:
    """Chunk a single page's text with a sliding window."""
    if not text:
        return []

    start = 0
    page_chunks: list[Chunk] = []
    while start < len(text):
        end = _find_cut(text, start, size)

        chunk_text = text[start:end]
        bbox = _span_bbox(start, end, text, bboxes)

        page_chunks.append(
            Chunk(
                chunk_id=_chunk_hash(chunk_text),
                doc_id=doc_id,
                filename=filename,
                page_number=page_number,
                text=chunk_text,
                chunk_index=0,
                bbox=bbox,
            )
        )

        if end >= len(text):
            break

        next_start = max(start + 1, end - overlap)
        start = next_start

    return page_chunks


def _find_cut(text: str, start: int, size: int) -> int:
    """Find a boundary-aware end index for a chunk starting at `start`."""
    hard_end = start + size
    if hard_end >= len(text):
        return len(text)

    for boundary in ("\n\n", "\n", " "):
        cut = text.rfind(boundary, start, hard_end)
        if cut != -1:
            return min(cut + len(boundary), len(text))

    return hard_end


def _span_bbox(start: int, end: int, text: str, bboxes: list[BBox]) -> BBox | None:
    """Compute the bounding box spanning the chunk's character range."""
    line_starts = _line_starts(text)
    if not line_starts:
        return None

    intersecting: list[BBox] = []
    for i, line_start in enumerate(line_starts):
        line_end = line_starts[i + 1] if i + 1 < len(line_starts) else len(text)
        if line_end > start and line_start < end:
            intersecting.append(bboxes[i])

    if not intersecting:
        return None

    return BBox(
        x0=min(b.x0 for b in intersecting),
        y0=min(b.y0 for b in intersecting),
        x1=max(b.x1 for b in intersecting),
        y1=max(b.y1 for b in intersecting),
    )


def _line_starts(text: str) -> list[int]:
    """Offsets of each line's first character."""
    starts: list[int] = []
    pos = 0
    while pos < len(text):
        starts.append(pos)
        nl = text.find("\n", pos)
        if nl == -1:
            break
        pos = nl + 1
    return starts


def _chunk_hash(text: str) -> str:
    """Deterministic UUIDv5 of chunk text — the idempotency key."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, digest))
