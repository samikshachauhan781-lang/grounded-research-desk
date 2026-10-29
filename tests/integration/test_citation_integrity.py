"""Citation integrity checks."""

from fastapi.testclient import TestClient


def test_citations_reference_retrieved_chunks_only(
    client: TestClient,
    sample_bytes: bytes,
) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("sample.md", sample_bytes, "text/markdown")},
    )
    document_id = upload.json()["document_id"]

    response = client.post(
        "/api/v1/ask",
        json={
            "question": "What command rolls back the database migration?",
            "document_ids": [document_id],
        },
    )
    assert response.status_code == 200
    body = response.json()
    chunks = client.get(f"/api/v1/documents/{document_id}/chunks")
    valid_ids = {item["chunk_id"] for item in chunks.json()["items"]}
    for citation in body["citations"]:
        assert citation["chunk_id"] in valid_ids
        assert citation["document_id"] == document_id
