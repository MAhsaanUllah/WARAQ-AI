"""M5 contract conformance tests.

The routes are exercised against a real app (TestClient). The LLM generation
is mocked so no API key is needed; the retrieval/rerank pipeline runs against
live Qdrant when available (skips otherwise).

These verify the *contract shapes* from docs/api-contract.md:
- upload → 201 with {document_id, filename, pages, chunks, status}
- query → 200 with {answer, sources[], processing_ms}
- stream-query → SSE event flow: status → answer_delta* → done{sources}
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import TEST_USER_ID


@pytest.fixture(scope="module")
def client():
    from app.core import auth

    app = create_app()

    async def _fake_current_user():
        return TEST_USER_ID

    app.dependency_overrides[auth.get_current_user] = _fake_current_user
    return TestClient(app)


@pytest.fixture
def pdf_bytes() -> bytes:
    """A tiny 1-page PDF with a UNIQUE paragraph so it doesn't collide with
    chunks indexed by other test modules in the shared collection."""
    import sys

    sys.path.insert(0, "tests")
    from conftest import _build_pdf, _wrap

    return _build_pdf(
        [_wrap("Waraq API contract test marker. Zephyr nebula quantum hybrid retrieval signals.")]
    )


def _upload(client: TestClient, pdf: bytes) -> dict:
    response = client.post(
        "/api/upload-doc",
        files={"file": ("test.pdf", pdf, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_upload_doc_contract_shape(client: TestClient, pdf_bytes: bytes) -> None:
    body = _upload(client, pdf_bytes)
    assert set(body.keys()) == {"document_id", "filename", "pages", "chunks", "status"}
    assert body["filename"] == "test.pdf"
    assert body["pages"] == 1
    assert body["chunks"] >= 1
    assert body["status"] == "indexed"


def test_upload_rejects_non_pdf(client: TestClient) -> None:
    response = client.post(
        "/api/upload-doc",
        files={"file": ("x.pdf", b"this is not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_upload_rejects_oversized(client: TestClient) -> None:
    big = b"x" * (51 * 1024 * 1024)
    response = client.post(
        "/api/upload-doc",
        files={"file": ("big.pdf", big, "application/pdf")},
    )
    assert response.status_code == 413


def test_query_contract_shape(client: TestClient, pdf_bytes: bytes) -> None:
    upload_body = _upload(client, pdf_bytes)

    from app.services.generation import generate_answer

    with pytest.MonkeyPatch.context() as mp:
        async def _fake_answer(query: str, chunks, web_context=None) -> str:
            return "Zephyr nebula quantum hybrid retrieval [1]."

        mp.setattr("app.api.routes.rag.generate_answer", _fake_answer)

        response = client.post("/api/query", json={"question": "What is quantum hybrid retrieval?"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert set(body.keys()) == {"answer", "sources", "processing_ms"}
        assert isinstance(body["processing_ms"], int)
        assert body["sources"], "sources must be non-empty"
        source = body["sources"][0]
        assert set(source.keys()) == {
            "document_id", "filename", "page", "chunk_hash", "bbox", "score", "snippet",
        }
        assert source["page"] >= 1
        # The source must belong to the doc we just uploaded (unique marker text).
        assert source["document_id"] == upload_body["document_id"]


def test_query_validation_empty_question(client: TestClient) -> None:
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 422


def test_stream_query_sse_event_flow(client: TestClient, pdf_bytes: bytes) -> None:
    from app.core.runtime_config import clear_llm_config

    clear_llm_config()  # deterministic: no runtime LLM provider/key
    _upload(client, pdf_bytes)

    from app.services.generation import stream_answer

    async def _fake_stream(query: str, chunks, web_context=None):
        for token in ["Hybrid ", "retrieval ", "works ", "[1]."]:
            yield token

    with pytest.MonkeyPatch.context() as mp:
        # stream_answer is imported at module top in rag.py → patch the route's
        # namespace, not the generation module (a re-import wouldn't re-fetch).
        mp.setattr("app.api.routes.rag.stream_answer", _fake_stream)

        response = client.get(
            "/api/stream-query",
            params={"question": "What is quantum hybrid retrieval?"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        text = response.text
        events = []
        for frame in text.strip().split("\n\n"):
            if not frame.strip():
                continue
            event_name = None
            data = None
            for line in frame.split("\n"):
                if line.startswith("event: "):
                    event_name = line[7:]
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
            events.append((event_name, data))

        names = [e[0] for e in events]
        # Contract invariants: answer_delta after status:generating; done last.
        assert names[0] == "status"
        assert "answer_delta" in names
        assert names[-1] == "done"
        gen_idx = next(i for i, (n, d) in enumerate(events) if n == "status" and d["stage"] == "generating")
        assert names.index("answer_delta") > gen_idx

        done = events[-1][1]
        assert "sources" in done
        assert done["sources"], "done must carry non-empty sources"
        assert "processing_ms" in done
        assert isinstance(done["processing_ms"], int)


def test_stream_query_error_event_on_empty_index(client: TestClient) -> None:
    """No matching docs → error SSE event, no done event."""
    from app.services.generation import stream_answer

    async def _fake_stream(query: str, chunks, web_context=None):
        yield "x"

    async def _no_candidates(request):
        return []

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.routes.rag.stream_answer", _fake_stream)
        mp.setattr("app.api.routes.rag.hybrid_search", _no_candidates)
        response = client.get("/api/stream-query", params={"question": "anything"})
        text = response.text
        assert "event: error" in text
        assert "event: done" not in text


# --- BYOK settings ---

def test_settings_get_returns_default_provider(client: TestClient) -> None:
    response = client.get("/api/settings")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"provider", "has_api_key", "search_provider", "has_search_key"}
    assert body["provider"] in {"deepseek", "gemini", "openai", "anthropic", "openrouter"}
    assert body["has_api_key"] is False  # no key in env or runtime
    assert body["search_provider"] is None
    assert body["has_search_key"] is False


def test_settings_put_sets_runtime_config(client: TestClient) -> None:
    from app.core.runtime_config import clear_llm_config

    clear_llm_config()  # deterministic start
    response = client.put(
        "/api/settings",
        json={"provider": "openrouter", "api_key": "sk-or-v1-test-key-123456"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openrouter"
    assert body["has_api_key"] is True

    # GET reflects it (key itself never returned).
    get_resp = client.get("/api/settings")
    assert get_resp.json()["provider"] == "openrouter"
    assert get_resp.json()["has_api_key"] is True
    assert "api_key" not in get_resp.json()

    clear_llm_config()


def test_settings_put_rejects_bad_provider(client: TestClient) -> None:
    response = client.put(
        "/api/settings",
        json={"provider": "not-a-provider", "api_key": "sk-test-12345678"},
    )
    assert response.status_code == 422


def test_settings_put_rejects_short_key(client: TestClient) -> None:
    response = client.put(
        "/api/settings",
        json={"provider": "deepseek", "api_key": "short"},
    )
    assert response.status_code == 422


# --- Multi-file upload ---

def test_upload_docs_batch(client: TestClient, pdf_bytes: bytes) -> None:
    """POST /api/upload-docs with multiple files → per-file results."""
    response = client.post(
        "/api/upload-docs",
        files=[
            ("files", ("a.pdf", pdf_bytes, "application/pdf")),
            ("files", ("b.pdf", pdf_bytes, "application/pdf")),
        ],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert set(body.keys()) == {"results", "total_pages", "total_chunks"}
    assert len(body["results"]) == 2
    assert body["results"][0]["filename"] == "a.pdf"
    assert body["results"][1]["filename"] == "b.pdf"
    assert body["total_pages"] == body["results"][0]["pages"] + body["results"][1]["pages"]
    assert body["total_chunks"] >= 2


def test_upload_docs_rejects_bad_file(client: TestClient) -> None:
    """One bad file in the batch → 400 with the filename in the detail."""
    response = client.post(
        "/api/upload-docs",
        files=[
            ("files", ("good.pdf", b"%PDF-1.7 fake", "application/pdf")),
        ],
    )
    # A malformed PDF is either rejected by pymupdf (400) or fails size... 
    # assert it's a 400 with an actionable message.
    assert response.status_code == 400
    assert "good.pdf" in response.json()["detail"]


def test_query_returns_clean_503_without_llm_key(client: TestClient) -> None:
    """No LLM key configured → 503 with actionable detail, not a 500."""
    from app.core.runtime_config import clear_llm_config
    from app.services.generation import generate_answer

    clear_llm_config()

    async def _fake_answer(query: str, chunks) -> str:
        return "never reached"

    # Ensure a doc exists so we get past retrieval to generation.
    import sys
    sys.path.insert(0, "tests")
    from conftest import _build_pdf, _wrap
    pdf = _build_pdf([_wrap("Zephyr nebula quantum retrieval marker doc.")])
    _upload(client, pdf)

    with pytest.MonkeyPatch.context() as mp:
        # Force the LLM-not-configured path even if env has a key.
        def _raise_no_key() -> tuple[str, str]:
            raise __import__("app.services.generation", fromlist=["LLMNotConfiguredError"]).LLMNotConfiguredError(
                "No LLM API key configured. Set it in the Settings page (BYOK) or add WARAQAI_LLM_API_KEY to .env."
            )

        mp.setattr("app.services.generation._resolve_model", _raise_no_key)
        response = client.post("/api/query", json={"question": "What is quantum retrieval?"})
        assert response.status_code == 503
        assert "detail" in response.json()
        assert "LLM API key" in response.json()["detail"]


# --- Web search ---

def test_settings_search_put(client: TestClient) -> None:
    from app.core.runtime_config import clear_llm_config

    clear_llm_config()
    response = client.put(
        "/api/settings/search",
        json={"provider": "tavily", "api_key": "tvly-test-key-12345678"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["search_provider"] == "tavily"
    assert body["has_search_key"] is True

    get_resp = client.get("/api/settings")
    assert get_resp.json()["search_provider"] == "tavily"
    assert get_resp.json()["has_search_key"] is True
    assert "api_key" not in get_resp.json()

    clear_llm_config()


def test_settings_search_rejects_bad_provider(client: TestClient) -> None:
    response = client.put(
        "/api/settings/search",
        json={"provider": "google", "api_key": "tvly-test-key-12345678"},
    )
    assert response.status_code == 422


def test_query_web_search_requires_key(client: TestClient, pdf_bytes: bytes) -> None:
    """use_web_search=true with no search key → clean 503, not 500."""
    from app.core.runtime_config import clear_llm_config

    clear_llm_config()
    _upload(client, pdf_bytes)

    response = client.post(
        "/api/query",
        json={"question": "What is quantum retrieval?", "use_web_search": True},
    )
    # Either the LLM key check or the search key check fires first — both are
    # clean 503s with guidance.
    assert response.status_code == 503
    assert "detail" in response.json()

    clear_llm_config()


def test_web_search_calls_provider(client: TestClient, pdf_bytes: bytes) -> None:
    """With a search key set, web results are fetched and passed to generation."""
    from unittest.mock import AsyncMock, patch

    from app.core.runtime_config import clear_llm_config

    clear_llm_config()
    _upload(client, pdf_bytes)

    # Mock web_search to return results without hitting the network.
    fake_results = [
        {"title": "Hybrid Retrieval Explained", "url": "https://example.com/hybrid", "snippet": "Hybrid retrieval fuses dense and sparse signals."},
    ]

    async def _fake_generate(query, chunks, web_context=None):
        # Assert the web context actually reached generation.
        assert web_context == fake_results
        return "Hybrid retrieval fuses signals [1] [2]."

    with patch("app.api.routes.rag.web_search", new=AsyncMock(return_value=fake_results)) as mock_search:
        with patch("app.api.routes.rag.search_configured", return_value=True):
            with patch("app.api.routes.rag.generate_answer", new=_fake_generate):
                response = client.post(
                    "/api/query",
                    json={"question": "What is hybrid retrieval?", "use_web_search": True},
                )
                mock_search.assert_awaited_once_with("What is hybrid retrieval?")

    assert response.status_code == 200, response.text
    assert "sources" in response.json()
    clear_llm_config()


def test_stream_query_web_search_status_event(client: TestClient, pdf_bytes: bytes) -> None:
    """SSE with use_web_search emits a 'searching' status event."""
    from unittest.mock import AsyncMock, patch

    from app.core.runtime_config import clear_llm_config

    clear_llm_config()
    _upload(client, pdf_bytes)

    fake_results = [{"title": "T", "url": "https://e.com", "snippet": "S"}]

    async def _fake_stream(query, chunks, web_context=None):
        yield "web-enabled answer"

    with patch("app.api.routes.rag.web_search", new=AsyncMock(return_value=fake_results)):
        with patch("app.api.routes.rag.search_configured", return_value=True):
            with patch("app.api.routes.rag.stream_answer", new=_fake_stream):
                response = client.get(
                    "/api/stream-query",
                    params={"question": "What is hybrid retrieval?", "use_web_search": "true"},
                )

    text = response.text
    assert "event: status" in text
    assert '"stage": "searching"' in text
    assert "event: done" in text
    clear_llm_config()
