"""Dense + sparse embeddings via FastEmbed (local, offline)."""

from __future__ import annotations

import asyncio
from threading import Lock

from fastembed import SparseEmbedding, SparseTextEmbedding, TextEmbedding

DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_MODEL = "Qdrant/bm25"

_dense: TextEmbedding | None = None
_sparse: SparseTextEmbedding | None = None
_lock = Lock()

def _get_dense() -> TextEmbedding:
    global _dense
    if _dense is None:
        with _lock:
            if _dense is None:
                _dense = TextEmbedding(model_name=DENSE_MODEL)
    return _dense

def _get_sparse() -> SparseTextEmbedding:
    global _sparse
    if _sparse is None:
        with _lock:
            if _sparse is None:
                _sparse = SparseTextEmbedding(model_name=SPARSE_MODEL)
    return _sparse

async def embed_dense(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts into dense vectors using ultra-lightweight local model."""
    if not texts:
        return []
    vectors = await asyncio.to_thread(lambda: list(_get_dense().embed(texts)))
    return [vec.tolist() for vec in vectors]


async def embed_sparse(texts: list[str]) -> list[dict]:
    """Embed a batch of texts into sparse (BM25) vectors."""
    if not texts:
        return []
    sparse_vecs: list[SparseEmbedding] = await asyncio.to_thread(
        lambda: list(_get_sparse().embed(texts))
    )
    return [
        {"indices": [int(i) for i in sv.indices], "values": [float(v) for v in sv.values]}
        for sv in sparse_vecs
    ]
