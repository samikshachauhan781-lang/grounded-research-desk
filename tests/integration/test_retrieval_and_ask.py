"""Retrieval and ask integration tests."""

from fastapi.testclient import TestClient


def _upload_sample(client: TestClient, sample_bytes: bytes) -> str:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("sample.md", sample_bytes, "text/markdown")},
    )
    assert response.status_code == 201
    return response.json()["document_id"]


def test_golden_retrieval_questions(client: TestClient, sample_bytes: bytes) -> None:
    document_id = _upload_sample(client, sample_bytes)
    q1 = client.post(
        "/api/v1/search",
        json={"query": "What command rolls back the database migration?", "document_ids": [document_id]},
    )
    assert q1.status_code == 200
    results = q1.json()["results"]
    assert results
    snippets = " ".join(r["snippet"].lower() for r in results)
    assert "flyway rollback" in snippets

    q2 = client.post(
        "/api/v1/search",
        json={
            "query": "When should we scale API replicas for checkout latency?",
            "document_ids": [document_id],
        },
    )
    assert q2.status_code == 200
    snippets2 = " ".join(r["snippet"].lower() for r in q2.json()["results"])
    assert "scale api replicas to 3" in snippets2


def test_ask_returns_citations(client: TestClient, sample_bytes: bytes) -> None:
    document_id = _upload_sample(client, sample_bytes)
    response = client.post(
        "/api/v1/ask",
        json={"question": "What command rolls back the database migration?", "document_ids": [document_id]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]
    assert body["citations"][0]["chunk_id"]
    assert body["insufficient_evidence"] is False


def test_ask_irrelevant_question_insufficient_evidence(
    client: TestClient,
    sample_bytes: bytes,
) -> None:
    document_id = _upload_sample(client, sample_bytes)
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "What is the capital of Mars colony Zephyr-9?",
            "document_ids": [document_id],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is True
    assert body["citations"] == []
