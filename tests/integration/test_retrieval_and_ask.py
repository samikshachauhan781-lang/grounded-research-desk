"""Retrieval and ask integration tests."""

from pathlib import Path

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
    answer = body["answer"].lower()
    assert "flyway rollback" in answer
    assert "based on the retrieved evidence" not in answer


def test_ask_file_question_answers_from_passage_not_title(
    client: TestClient,
    project_root: Path,
) -> None:
    fixture = (project_root / "tests" / "fixtures" / "timeline_feature.md").read_bytes()
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("timeline_feature.md", fixture, "text/markdown")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["document_id"]
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "Which file contains all the tests for the new timeline functionality?",
            "document_ids": [document_id],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is False
    assert body["citations"]
    answer = body["answer"]
    assert "test_day7_timeline.py" in answer
    assert "timeline functionality" in answer.lower()
    assert "394 lines" not in answer


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


def test_ask_file_question_vague_overlap_returns_insufficient(
    client: TestClient,
    project_root: Path,
) -> None:
    fixture = (project_root / "tests" / "fixtures" / "vague_timeline_overview.md").read_bytes()
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("vague_timeline_overview.md", fixture, "text/markdown")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["document_id"]
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "Which file contains all the tests for the new timeline functionality?",
            "document_ids": [document_id],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is True
    assert body["citations"] == []
    assert "do not contain enough evidence" in body["answer"].lower()


def test_ask_citation_matches_winning_chunk_not_first_retrieval_rank(
    client: TestClient,
    project_root: Path,
) -> None:
    """Chunk B holds the filename answer; citation must reference B, not metadata chunk A."""
    fixture = (project_root / "tests" / "fixtures" / "timeline_feature.md").read_bytes()
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("timeline_feature.md", fixture, "text/markdown")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["document_id"]
    chunks_resp = client.get(f"/api/v1/documents/{document_id}/chunks")
    assert chunks_resp.status_code == 200
    chunk_items = chunks_resp.json()["items"]
    assert len(chunk_items) >= 1

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "Which file contains all the tests for the new timeline functionality?",
            "document_ids": [document_id],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is False
    assert body["citations"]
    cited_id = body["citations"][0]["chunk_id"]
    assert "test_day7_timeline.py" in body["answer"]
    assert f"[chunk:{cited_id}]" in body["answer"]
    assert "394 lines" not in body["answer"]
