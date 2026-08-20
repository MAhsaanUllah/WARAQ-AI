"""M7/M8 integration tests: resource listing + tenant isolation.

Requires Dockerized Qdrant (`docker compose up -d`); skips cleanly if down.
"""

import asyncio

import pytest

from app.core.config import get_settings
from app.core.qdrant import get_client
from app.models.ingestion import BBox, Chunk, Document, Page
from app.models.retrieval import QueryRequest
from app.services.documents import list_documents
from app.services.indexing import delete_document, ensure_collection, index_document
from app.services.retrieval import _tenant_filter, hybrid_search

# Use dedicated users NOT shared with the API route tests, so their uploads
# (same collection, same TEST_USER_ID) can't pollute these isolation tests.
USER_A = "tenant-user-alpha"
USER_B = "tenant-user-beta"


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


def _doc(doc_id: str, filename: str, text: str) -> Document:
    from app.services.chunking import _chunk_hash

    return Document(
        doc_id=doc_id,
        filename=filename,
        pages=[Page(page_number=1, text=text)],
        chunks=[
            Chunk(
                chunk_id=_chunk_hash(text),
                doc_id=doc_id,
                filename=filename,
                page_number=1,
                text=text,
                chunk_index=0,
                bbox=BBox(x0=0, y0=0, x1=100, y1=20),
            )
        ],
    )


@requires_qdrant
async def test_list_documents_scoped_to_user() -> None:
    await ensure_collection()
    await index_document(_doc("m8-doc-a", "alpha.pdf", "Alpha document about hybrid retrieval."), USER_A)
    await index_document(_doc("m8-doc-b", "beta.pdf", "Beta document about quantum computing."), USER_B)

    docs_a = await list_documents(USER_A)
    by_id = {d.document_id: d for d in docs_a}

    # User A sees only their own doc.
    assert "m8-doc-a" in by_id
    assert by_id["m8-doc-a"].filename == "alpha.pdf"
    assert by_id["m8-doc-a"].chunks == 1
    assert by_id["m8-doc-a"].pages == 1
    assert "m8-doc-b" not in by_id  # tenant isolation

    await delete_document("m8-doc-a")
    await delete_document("m8-doc-b")


@requires_qdrant
async def test_hybrid_search_tenant_isolation() -> None:
    await ensure_collection()
    # Unique marker text so no other test module's docs collide.
    await index_document(_doc("m8-scope-a", "scope-a.pdf", "Waraq tenant isolation zqxvone marker alpha."), USER_A)
    await index_document(_doc("m8-scope-b", "scope-b.pdf", "Waraq tenant isolation zqxvone marker beta."), USER_B)

    # User A searching: only A's doc appears, even though B has matching content.
    request = QueryRequest(question="Waraq tenant isolation zqxvone")
    results_a = await hybrid_search(request, USER_A)
    assert results_a
    assert all(r.doc_id == "m8-scope-a" for r in results_a)

    # Scoped to a doc the user doesn't own → no results (no leak).
    request_other = QueryRequest(question="Waraq tenant isolation zqxvone", document_ids=["m8-scope-b"])
    results_other = await hybrid_search(request_other, USER_A)
    assert not results_other

    # User B sees only B.
    results_b = await hybrid_search(request, USER_B)
    assert results_b
    assert all(r.doc_id == "m8-scope-b" for r in results_b)

    await delete_document("m8-scope-a")
    await delete_document("m8-scope-b")


@requires_qdrant
async def test_tenant_filter_always_has_user() -> None:
    # The strict user_id condition is ALWAYS present (never optional).
    f1 = _tenant_filter("user-x", QueryRequest(question="q"))
    assert any(c.key == "user_id" for c in f1.must)

    f2 = _tenant_filter("user-x", QueryRequest(question="q", document_ids=["a"]))
    keys = {c.key for c in f2.must}
    assert "user_id" in keys
    assert "doc_id" in keys
