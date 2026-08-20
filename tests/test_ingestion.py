"""Ingestion orchestrator tests: parse_and_chunk end to end.

parse_and_chunk is async (M3: embed + upsert are I/O bound), so these are
asyncio-mode tests (pytest-asyncio, configured `asyncio_mode = auto`).
"""

from app.services.ingestion import parse_and_chunk


async def test_parse_and_chunk_returns_ingest_result(one_page_pdf: bytes) -> None:
    document, result = await parse_and_chunk(one_page_pdf, "one_page.pdf")
    assert result.document_id == document.doc_id
    assert result.filename == "one_page.pdf"
    assert result.pages == len(document.pages) == 1
    assert result.chunks >= 1
    assert result.status == "indexed"
    # M3: chunks are attached to the document for embedding.
    assert len(document.chunks) == result.chunks


async def test_ingest_result_counts_match(three_page_pdf: bytes) -> None:
    document, result = await parse_and_chunk(three_page_pdf, "three_page.pdf")
    assert result.pages == 3
    assert result.chunks >= 3
    assert len(document.chunks) == result.chunks
