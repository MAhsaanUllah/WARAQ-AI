"""Health endpoint contract: 200 with the documented JSON shape.

⚠️ These tests use the app factory directly (TestClient) so they need no
running Qdrant — the health endpoint reports "unavailable" instead of failing.
"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_contract_shape() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]  # non-empty
    assert body["qdrant"] in {"connected", "unavailable"}


def test_health_endpoint_never_blocks_without_qdrant() -> None:
    client = TestClient(create_app())
    # Must respond quickly even when the vector store is down.
    response = client.get("/health")
    assert response.status_code == 200
