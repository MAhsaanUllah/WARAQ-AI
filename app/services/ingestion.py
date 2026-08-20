"""Stage 1 orchestrator: extract → chunk → index."""

from __future__ import annotations

from app.models.ingestion import Document, IngestResult
from app.services.chunking import chunk_document
from app.services.extraction import extract_document
from app.services.indexing import index_document


async def ingest_document(data: bytes, filename: str, user_id: str) -> IngestResult:
    """Extract, chunk, embed, and upsert a PDF. Returns the ingest result."""
    document = extract_document(data, filename)
    chunks = chunk_document(document)
    document.chunks = chunks

    chunk_count = await index_document(document, user_id)

    return IngestResult(
        document_id=document.doc_id,
        filename=filename,
        pages=len(document.pages),
        chunks=chunk_count,
    )


async def parse_and_chunk(data: bytes, filename: str) -> tuple[Document, IngestResult]:
    """Extract and chunk a PDF without indexing (for tests and callers)."""
    document = extract_document(data, filename)
    chunks = chunk_document(document)
    document.chunks = chunks

    result = IngestResult(
        document_id=document.doc_id,
        filename=filename,
        pages=len(document.pages),
        chunks=len(chunks),
    )
    return document, result
