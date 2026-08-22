"""Dense + sparse embeddings via FastEmbed (local, offline)."""

from __future__ import annotations

import asyncio
from threading import Lock

from fastembed import SparseEmbedding, SparseTextEmbedding, TextEmbedding

DENSE_MODEL = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"

_dense: TextEmbedding | None = None
_sparse: SparseTextEmbedding | None = None
_lock = Lock()

from litellm import embedding as litellm_embedding
from app.core.config import get_settings

async def embed_dense(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts into dense vectors using Cloud API (LiteLLM) to save RAM."""
    if not texts:
        return []
        
    settings = get_settings()
    # If user provided gemini API key, we use gemini/text-embedding-004
    # LiteLLM routes automatically based on the model name prefix
    model_name = "gemini/text-embedding-004"
    api_key = settings.llm_api_key.get_secret_value()
    
    # Run in thread since litellm is synchronous
    response = await asyncio.to_thread(
        litellm_embedding,
        model=model_name,
        input=texts,
        api_key=api_key
    )
    
    return [item["embedding"] for item in response["data"]]


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
