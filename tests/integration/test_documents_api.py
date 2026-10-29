"""Document API integration tests."""

from fastapi.testclient import TestClient


def test_upload_list_and_get_document(client: TestClient, sample_bytes: bytes) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("sample.md", sample_bytes, "text/markdown")},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["chunk_count"] >= 1
    document_id = body["document_id"]

    listing = client.get("/api/v1/documents")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    detail = client.get(f"/api/v1/documents/{document_id}")
    assert detail.status_code == 200
    assert detail.json()["processing_status"] == "completed"

    chunks = client.get(f"/api/v1/documents/{document_id}/chunks")
    assert chunks.status_code == 200
    assert chunks.json()["total"] >= 1


def test_upload_rejects_invalid_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("bad.exe", b"data", "application/octet-stream")},
    )
    assert response.status_code == 422


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("empty.md", b"", "text/markdown")},
    )
    assert response.status_code == 422
