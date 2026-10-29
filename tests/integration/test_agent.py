"""Agent integration test."""

from fastapi.testclient import TestClient


def test_agent_research_flow(client: TestClient, sample_bytes: bytes) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("sample.md", sample_bytes, "text/markdown")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["document_id"]

    response = client.post(
        "/api/v1/research",
        json={"goal": "What command rolls back the database migration?", "document_ids": [document_id]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["steps"]
