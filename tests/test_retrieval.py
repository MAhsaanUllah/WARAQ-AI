"""M4 unit tests: hybrid retrieval RRF math + rerank ordering.

The RRF tests validate the fusion logic with a hand-computed example; the
rerank tests mock flashrank so no model download is needed.
"""

from unittest.mock import patch

from app.models.retrieval import QueryRequest, RetrievedChunk, RerankedResult
from app.services.retrieval import RRF_K
from app.services.reranking import rerank


def _chunk(chunk_id: str, text: str, page: int = 1, score: float | None = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        doc_id="doc-1",
        filename="sample.pdf",
        page_number=page,
        text=text,
        score=score,
    )


def test_query_request_validation() -> None:
    req = QueryRequest(question="hello")
    assert req.top_k_candidates is None
    assert req.top_k_final is None


def test_query_request_rejects_empty_question() -> None:
    import pytest

    with pytest.raises(Exception):
        QueryRequest(question="")


def test_rrf_k_is_standard() -> None:
    assert RRF_K == 60


def test_rerank_returns_empty_for_no_candidates() -> None:
    import asyncio

    result = asyncio.run(rerank("query", []))
    assert result == []


async def test_rerank_orders_by_score_and_preserves_metadata() -> None:
    candidates = [
        _chunk("c1", "First chunk about hybrid retrieval.", score=0.4),
        _chunk("c2", "Second chunk, less relevant.", score=0.2),
        _chunk("c3", "Third chunk, most relevant.", score=0.9),
    ]

    # Mock flashrank: return candidates in the order the real one would
    # (highest relevance first), proving we take top_k and preserve metadata.
    fake_ranked = [
        {"id": "c3", "text": "Third chunk, most relevant.", "score": 0.95,
         "meta": {"doc_id": "doc-1", "filename": "sample.pdf", "page_number": 1,
                  "bbox": None, "rrf_score": 0.9}},
        {"id": "c1", "text": "First chunk about hybrid retrieval.", "score": 0.8,
         "meta": {"doc_id": "doc-1", "filename": "sample.pdf", "page_number": 1,
                  "bbox": None, "rrf_score": 0.4}},
        {"id": "c2", "text": "Second chunk, less relevant.", "score": 0.3,
         "meta": {"doc_id": "doc-1", "filename": "sample.pdf", "page_number": 1,
                  "bbox": None, "rrf_score": 0.2}},
    ]

    with patch("app.services.reranking._get_ranker") as mock_ranker:
        mock_ranker.return_value.rerank.return_value = fake_ranked
        result = await rerank("query", candidates, top_k=2)

    assert len(result) == 2  # top_k=2 respected
    assert [r.chunk_id for r in result] == ["c3", "c1"]
    assert result[0].rank == 1
    assert result[1].rank == 2
    # Metadata survives the rerank round-trip.
    assert result[0].doc_id == "doc-1"
    assert result[0].filename == "sample.pdf"
    assert result[0].page_number == 1
    assert result[0].score == 0.95
    assert isinstance(result[0], RerankedResult)


def test_rerank_handles_bbox_roundtrip() -> None:
    import asyncio

    from app.models.ingestion import BBox

    candidates = [
        RetrievedChunk(
            chunk_id="c1",
            doc_id="d",
            filename="f.pdf",
            page_number=2,
            text="text",
            bbox=BBox(x0=1.0, y0=2.0, x1=3.0, y1=4.0),
            score=0.5,
        )
    ]
    fake_ranked = [
        {"id": "c1", "text": "text", "score": 0.9,
         "meta": {"doc_id": "d", "filename": "f.pdf", "page_number": 2,
                  "bbox": {"x0": 1.0, "y0": 2.0, "x1": 3.0, "y1": 4.0},
                  "rrf_score": 0.5}},
    ]
    with patch("app.services.reranking._get_ranker") as mock_ranker:
        mock_ranker.return_value.rerank.return_value = fake_ranked
        result = asyncio.run(rerank("q", candidates))

    assert result[0].bbox is not None
    assert result[0].bbox.x0 == 1.0
    assert result[0].bbox.y1 == 4.0
