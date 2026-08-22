"""Resource listing — enumerate indexed documents from Qdrant payloads."""

from __future__ import annotations

from collections import defaultdict

from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.config import get_settings
from app.core.qdrant import get_client
from app.models.api import DocumentInfo

SCROLL_PAGE_SIZE = 100


async def list_documents(user_id: str) -> list[DocumentInfo]:
    """Return one DocumentInfo per document owned by `user_id`."""
    client = get_client()
    collection = get_settings().qdrant_collection
    
    if not await client.collection_exists(collection):
        return []

    tenant_filter = Filter(
        must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
    )

    docs: dict[str, dict] = defaultdict(lambda: {"filename": "", "pages": set(), "chunks": 0})

    next_offset: object | None = None
    while True:
        points, next_offset = await client.scroll(
            collection_name=collection,
            limit=SCROLL_PAGE_SIZE,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
            scroll_filter=tenant_filter,
        )
        for point in points:
            payload = point.payload or {}
            doc_id = payload.get("doc_id")
            if not doc_id:
                continue
            entry = docs[doc_id]
            entry["filename"] = payload.get("filename", entry["filename"])
            entry["chunks"] += 1
            page = payload.get("page_number")
            if page:
                entry["pages"].add(page)

        if next_offset is None:
            break

    return [
        DocumentInfo(
            document_id=doc_id,
            filename=data["filename"],
            pages=len(data["pages"]),
            chunks=data["chunks"],
        )
        for doc_id, data in sorted(docs.items())
    ]
