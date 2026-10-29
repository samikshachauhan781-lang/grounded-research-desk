"""Health endpoint tests (T-1)."""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "grounded-research-desk-test"
    assert body["version"] == "0.1.0"


def test_health_content_type_is_json(client: TestClient) -> None:
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
