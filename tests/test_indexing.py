"""M3 integration tests: hybrid indexing against a live Qdrant.

These require the Dockerized Qdrant (`docker compose up -d`). If it's not
reachable, they skip with a clear message — they never fail a dev loop that
doesn't have the vector store running.
"""

import pytest

from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.config import get_settings
from app.core.qdrant import get_client
from app.models.ingestion import BBox, Chunk, Document, Page
from app.services.indexing import (
    BATCH_SIZE,
    delete_document,
    ensure_collection,
    index_document,
)


def _count_filter(doc_id: str) -> Filter:
    return Filter(
        must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
    )


def _qdrant_up() -> bool:
    import asyncio

    async def _ping() -> bool:
        try:
            await get_client().info()
            return True
        except Exception:  # noqa: BLE001
            return False

    return asyncio.run(_ping())


requires_qdrant = pytest.mark.skipif(
    not _qdrant_up(),
    reason="Qdrant not reachable — run `docker compose up -d` first",
)

COLLECTION = get_settings().qdrant_collection


def _sample_document(doc_id: str) -> Document:
    """A small 2-page document with deterministic chunks."""
    return Document(
        doc_id=doc_id,
        filename="sample.pdf",
        pages=[
            Page(
                page_number=1,
                text="The quick brown fox jumps over the lazy dog. Hybrid retrieval fuses dense and sparse signals.",
                bboxes=[BBox(x0=0, y0=0, x1=100, y1=20)],
            ),
            Page(
                page_number=2,
                text="Citations are deterministic when chunks never span pages.",
                bboxes=[BBox(x0=0, y0=0, x1=100, y1=20)],
            ),
        ],
        chunks=[
            Chunk(
                chunk_id="11111111-1111-1111-1111-111111111111",
                doc_id=doc_id,
                filename="sample.pdf",
                page_number=1,
                text="The quick brown fox jumps over the lazy dog. Hybrid retrieval fuses dense and sparse signals.",
                chunk_index=0,
                bbox=BBox(x0=0, y0=0, x1=100, y1=20),
            ),
            Chunk(
                chunk_id="22222222-2222-2222-2222-222222222222",
                doc_id=doc_id,
                filename="sample.pdf",
                page_number=2,
                text="Citations are deterministic when chunks never span pages.",
                chunk_index=1,
                bbox=BBox(x0=0, y0=0, x1=100, y1=20),
            ),
        ],
    )


@requires_qdrant
async def test_ensure_collection_creates_named_vectors() -> None:
    await ensure_collection()
    client = get_client()
    info = await client.get_collection(COLLECTION)
    assert "dense" in info.config.params.vectors
    assert "sparse" in info.config.params.sparse_vectors


@requires_qdrant
async def test_index_document_upserts_points() -> None:
    doc = _sample_document("integ-test-1")
    count = await index_document(doc, "test-user")
    assert count == 2

    client = get_client()
    points = await client.retrieve(
        COLLECTION,
        ids=["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"],
        with_payload=True,
    )
    assert len(points) == 2
    for p in points:
        assert p.payload["doc_id"] == "integ-test-1"
        assert p.payload["page_number"] in {1, 2}
        assert p.payload["filename"] == "sample.pdf"
        assert "text" in p.payload
    await delete_document("integ-test-1")


@requires_qdrant
async def test_index_is_idempotent_by_chunk_hash() -> None:
    doc = _sample_document("integ-test-2")
    await index_document(doc, "test-user")
    await index_document(doc, "test-user")  # re-ingest same content

    client = get_client()
    count = await client.count(
        COLLECTION,
        exact=True,
        count_filter=_count_filter("integ-test-2"),
    )
    # Same chunk hashes → upserts overwrite, never duplicate.
    assert count.count == 2
    await delete_document("integ-test-2")


@requires_qdrant
async def test_delete_document_removes_all_chunks() -> None:
    doc = _sample_document("integ-test-3")
    await index_document(doc, "test-user")
    await delete_document("integ-test-3")

    client = get_client()
    count = await client.count(
        COLLECTION,
        exact=True,
        count_filter=_count_filter("integ-test-3"),
    )
    assert count.count == 0


@requires_qdrant
def test_batch_size_sanity() -> None:
    assert BATCH_SIZE <= 64  # qdrant-client gRPC limit
    assert BATCH_SIZE > 0
