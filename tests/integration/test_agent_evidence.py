"""Agent evidence sufficiency alignment with /ask."""

from fastapi.testclient import TestClient


def test_agent_irrelevant_goal_insufficient_evidence(
    client: TestClient,
    sample_bytes: bytes,
) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("sample.md", sample_bytes, "text/markdown")},
    )
    document_id = upload.json()["document_id"]

    response = client.post(
        "/api/v1/research",
        json={
            "goal": "What is the capital of Mars colony Zephyr-9?",
            "document_ids": [document_id],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"] == []
    assert "do not contain enough evidence" in body["answer"].lower()
