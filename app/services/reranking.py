"""Cross-encoder reranking with flashrank."""

from __future__ import annotations

import asyncio

from flashrank import Ranker, RerankRequest

from app.models.retrieval import RerankedResult, RetrievedChunk

RERANK_MODEL = "ms-marco-MiniLM-L-12-v2"

_ranker: Ranker | None = None


def _get_ranker():
    pass

async def rerank(query: str, candidates: list[RetrievedChunk], top_k: int = 5) -> list[RerankedResult]:
    """Bypass cross-encoder reranking to save memory on free tier. Returns top `top_k`."""
    if not candidates:
        return []

    results: list[RerankedResult] = []
    # Candidates are already sorted by RRF score from hybrid search
    for i, c in enumerate(candidates[:top_k], start=1):
        results.append(
            RerankedResult(
                chunk_id=c.chunk_id,
                doc_id=c.doc_id,
                filename=c.filename,
                page_number=c.page_number,
                text=c.text,
                bbox=c.bbox,
                score=c.score,
                rank=i,
            )
        )
    return results
