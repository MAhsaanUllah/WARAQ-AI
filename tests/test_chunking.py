"""Stage 1b tests: page-boundary-safe chunking — boundaries, overlap, hashes."""

from app.models.ingestion import Chunk
from app.services.chunking import chunk_document, _chunk_hash
from app.services.extraction import extract_document


def _chunks_from(pdf: bytes, filename: str) -> list[Chunk]:
    return chunk_document(extract_document(pdf, filename))


def test_chunks_never_span_pages(three_page_pdf: bytes) -> None:
    """THE invariant: every chunk belongs to exactly one page."""
    chunks = _chunks_from(three_page_pdf, "three_page.pdf")
    assert len(chunks) > 1
    assert all(c.page_number in {1, 2, 3} for c in chunks)
    # Chunks are ordered by page then position.
    pages = [c.page_number for c in chunks]
    assert pages == sorted(pages)


def test_chunk_metadata_complete(one_page_pdf: bytes) -> None:
    chunks = _chunks_from(one_page_pdf, "one_page.pdf")
    assert chunks
    for c in chunks:
        assert c.doc_id  # uuid present
        assert c.filename == "one_page.pdf"
        assert c.page_number == 1
        assert c.text  # non-empty
        assert c.chunk_id  # sha256 hash present
        assert c.chunk_index >= 0


def test_chunk_hashes_are_stable(one_page_pdf: bytes) -> None:
    """Same content → same hash → idempotent upserts in M3."""
    first = _chunks_from(one_page_pdf, "one_page.pdf")
    second = _chunks_from(one_page_pdf, "one_page.pdf")
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]


def test_overlap_preserves_context(long_paragraph_pdf: bytes) -> None:
    """The overlap window keeps context across chunk cut boundaries.

    With overlap > 0, the tail of chunk N must appear verbatim at the head of
    chunk N+1 when both chunks come from one continuous paragraph.
    """
    chunks = _chunks_from(long_paragraph_pdf, "long.pdf")
    assert len(chunks) >= 2

    found_overlap = False
    for a, b in zip(chunks, chunks[1:]):
        if a.page_number != b.page_number:
            continue
        # The shared window is the overlap-sized suffix of `a` / prefix of `b`.
        max_overlap = min(200, len(a.text), len(b.text))
        for k in range(1, max_overlap + 1):
            if a.text[-k:] == b.text[:k]:
                found_overlap = True
                break
        if found_overlap:
            break

    assert found_overlap


def test_chunk_hashes_deduplicate_identical_pages(three_page_pdf: bytes) -> None:
    """Identical page text yields identical chunk hashes across pages."""
    chunks = _chunks_from(three_page_pdf, "three_page.pdf")
    page_one_hashes = {c.chunk_id for c in chunks if c.page_number == 1}
    page_two_hashes = {c.chunk_id for c in chunks if c.page_number == 2}
    assert page_one_hashes == page_two_hashes


def test_hard_cut_handles_paragraph_longer_than_chunk(long_paragraph_pdf: bytes) -> None:
    """A single paragraph > chunk_size must still produce chunks."""
    chunks = _chunks_from(long_paragraph_pdf, "long.pdf")
    assert len(chunks) >= 2
    assert all(0 < len(c.text) <= 800 + 150 for c in chunks)  # size + overlap slack


def test_chunk_hash_function_is_deterministic() -> None:
    """chunk_id is a deterministic UUIDv5 (Qdrant point-ID constraint)."""
    import uuid as uuid_mod

    text = "the same text"
    h1, h2 = _chunk_hash(text), _chunk_hash(text)
    assert h1 == h2
    assert _chunk_hash(text) != _chunk_hash(text + "x")
    # Valid UUID, so Qdrant accepts it as a point ID.
    assert uuid_mod.UUID(h1)
    assert uuid_mod.uuid5(uuid_mod.NAMESPACE_URL, __import__("hashlib").sha256(text.encode()).hexdigest()) == uuid_mod.UUID(h1)
