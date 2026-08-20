"""Hybrid retrieval — dense + sparse query fused via RRF."""

from __future__ import annotations

from qdrant_client.models import (
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchAny,
    MatchValue,
    Prefetch,
)

from app.core.config import get_settings
from app.core.qdrant import get_client
from app.models.retrieval import QueryRequest, RetrievedChunk
from app.services.embeddings import embed_dense, embed_sparse

RRF_K = 60


def _tenant_filter(user_id: str, request: QueryRequest) -> Filter:
    """Strict tenant isolation filter: user_id always, document_ids if given."""
    conditions = [
        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
    ]
    if request.document_ids:
        conditions.append(
            FieldCondition(
                key="doc_id",
                match=MatchAny(any=request.document_ids),
            )
        )
    return Filter(must=conditions)


async def hybrid_search(request: QueryRequest, user_id: str) -> list[RetrievedChunk]:
    """Run dense + sparse prefetch and fuse with RRF. Returns top-k candidates."""
    settings = get_settings()
    top_k = request.top_k_candidates or settings.top_k_candidates
    tenant_filter = _tenant_filter(user_id, request)

    (dense_q,) = await embed_dense([request.question])
    (sparse_q,) = await embed_sparse([request.question])

    response = await get_client().query_points(
        collection_name=settings.qdrant_collection,
        prefetch=[
            Prefetch(
                query=dense_q,
                using="dense",
                limit=top_k,
                filter=tenant_filter,
            ),
            Prefetch(
                query=sparse_q,
                using="sparse",
                limit=top_k,
                filter=tenant_filter,
            ),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
        with_payload=True,
        with_vectors=False,
    )

    return [_to_retrieved(p) for p in response.points]


def _to_retrieved(point) -> RetrievedChunk:
    """Map a Qdrant scored point to the domain model."""
    payload = point.payload or {}
    return RetrievedChunk(
        chunk_id=str(point.id),
        doc_id=payload.get("doc_id", ""),
        filename=payload.get("filename", ""),
        page_number=payload.get("page_number", 1),
        text=payload.get("text", ""),
        bbox=payload.get("bbox"),
        score=point.score,
    )
