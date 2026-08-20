"""M4 integration test: ingest → hybrid search → rerank against live Qdrant.

Requires Dockerized Qdrant (`docker compose up -d`); skips cleanly if down.
Also requires the FastEmbed + flashrank ONNX models (downloaded on first use).
"""

import asyncio

import pytest

from app.core.config import get_settings
from app.core.qdrant import get_client
from app.models.ingestion import BBox, Chunk, Document, Page
from app.models.retrieval import QueryRequest
from app.services.indexing import delete_document, ensure_collection, index_document
from app.services.reranking import rerank
from app.services.retrieval import hybrid_search


def _qdrant_up() -> bool:
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
DOC_ID = "m4-integration-doc"


def _build_document() -> Document:
    """Two pages: one about hybrid retrieval, one about fishing."""
    return Document(
        doc_id=DOC_ID,
        filename="m4-sample.pdf",
        pages=[
            Page(page_number=1, text="Hybrid retrieval fuses dense and sparse signals."),
            Page(page_number=2, text="Fishing requires patience and a good rod."),
        ],
        chunks=[
            Chunk(
                chunk_id="33333333-3333-3333-3333-333333333333",
                doc_id=DOC_ID,
                filename="m4-sample.pdf",
                page_number=1,
                text="Hybrid retrieval fuses dense and sparse signals for better recall.",
                chunk_index=0,
                bbox=BBox(x0=0, y0=0, x1=100, y1=20),
            ),
            Chunk(
                chunk_id="44444444-4444-4444-4444-444444444444",
                doc_id=DOC_ID,
                filename="m4-sample.pdf",
                page_number=2,
                text="Fishing requires patience and a good rod on a calm lake.",
                chunk_index=1,
                bbox=BBox(x0=0, y0=0, x1=100, y1=20),
            ),
        ],
    )


@requires_qdrant
async def test_hybrid_search_returns_candidates() -> None:
    await ensure_collection()
    await index_document(_build_document(), "test-user")

    request = QueryRequest(question="What fuses dense and sparse signals?")
    candidates = await hybrid_search(request, "test-user")

    assert candidates
    assert all(c.page_number >= 1 for c in candidates)
    # The retrieval-related chunk should rank at or near the top.
    assert candidates[0].text  # non-empty
    assert candidates[0].doc_id == DOC_ID

    await delete_document(DOC_ID)


@requires_qdrant
async def test_full_pipeline_retrieve_rerank() -> None:
    await ensure_collection()
    await index_document(_build_document(), "test-user")

    request = QueryRequest(question="What fuses dense and sparse signals?", top_k_candidates=10, top_k_final=2)
    candidates = await hybrid_search(request, "test-user")
    reranked = await rerank(request.question, candidates, top_k=2)

    assert reranked
    assert len(reranked) <= 2
    assert reranked[0].rank == 1
    # Reranked scores are cross-encoder relevance in [0, 1].
    assert 0.0 <= reranked[0].score <= 1.0
    # Metadata survived the whole pipeline. The shared collection may hold
    # chunks from other test modules, so assert our doc appears in the
    # reranked set (it's the most relevant to this exact question).
    assert any(r.doc_id == DOC_ID for r in reranked)

    await delete_document(DOC_ID)
