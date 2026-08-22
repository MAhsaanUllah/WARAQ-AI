"""Hybrid indexing into Qdrant (dense + sparse named vectors)."""

from __future__ import annotations

from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from app.core.config import get_settings
from app.core.qdrant import get_client
from app.models.ingestion import Chunk, Document
from app.services.embeddings import embed_dense, embed_sparse

DENSE_DIM = 768
BATCH_SIZE = 32


async def ensure_collection() -> None:
    """Create the collection if missing, with dense + sparse named vectors."""
    settings = get_settings()
    client = get_client()
    if await client.collection_exists(settings.qdrant_collection):
        return

    await client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config={
            "dense": VectorParams(size=DENSE_DIM, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(),
        },
    )


async def index_document(document: Document, user_id: str) -> int:
    """Embed and upsert all chunks of a document, tagged with the owner."""
    await ensure_collection()

    chunks = document.chunks
    if not chunks:
        return 0

    dense = await embed_dense([c.text for c in chunks])
    sparse = await embed_sparse([c.text for c in chunks])

    points: list[PointStruct] = []
    for chunk, d_vec, s_vec in zip(chunks, dense, sparse):
        points.append(
            PointStruct(
                id=chunk.chunk_id,
                vector={
                    "dense": d_vec,
                    "sparse": SparseVector(
                        indices=s_vec["indices"],
                        values=s_vec["values"],
                    ),
                },
                payload={
                    "doc_id": chunk.doc_id,
                    "filename": chunk.filename,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "bbox": chunk.bbox.model_dump() if chunk.bbox else None,
                    "user_id": user_id,
                },
            )
        )

    client = get_client()
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i : i + BATCH_SIZE]
        await client.upsert(
            collection_name=get_settings().qdrant_collection,
            points=batch,
        )

    return len(chunks)


async def delete_document(doc_id: str) -> None:
    """Remove every chunk belonging to a document (payload-filter delete)."""
    client = get_client()
    await client.delete(
        collection_name=get_settings().qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )
