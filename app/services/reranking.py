"""Cross-encoder reranking with flashrank."""

from __future__ import annotations

import asyncio

from flashrank import Ranker, RerankRequest

from app.models.retrieval import RerankedResult, RetrievedChunk

RERANK_MODEL = "ms-marco-MiniLM-L-12-v2"

_ranker: Ranker | None = None


def _get_ranker() -> Ranker:
    global _ranker
    if _ranker is None:
        _ranker = Ranker(model_name=RERANK_MODEL)
    return _ranker


async def rerank(query: str, candidates: list[RetrievedChunk], top_k: int = 5) -> list[RerankedResult]:
    """Rerank candidates with a cross-encoder and return the top `top_k`."""
    if not candidates:
        return []

    passages = [
        {
            "id": c.chunk_id,
            "text": c.text,
            "meta": {
                "doc_id": c.doc_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "bbox": c.bbox.model_dump() if c.bbox else None,
                "rrf_score": c.score,
            },
        }
        for c in candidates
    ]

    request = RerankRequest(query=query, passages=passages)
    ranked = await asyncio.to_thread(_get_ranker().rerank, request)

    results: list[RerankedResult] = []
    for i, item in enumerate(ranked[:top_k], start=1):
        meta = item.get("meta", {})
        results.append(
            RerankedResult(
                chunk_id=item["id"],
                doc_id=meta.get("doc_id", ""),
                filename=meta.get("filename", ""),
                page_number=meta.get("page_number", 1),
                text=item["text"],
                bbox=meta.get("bbox"),
                score=float(item["score"]),
                rank=i,
            )
        )
    return results
