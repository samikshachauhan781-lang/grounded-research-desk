"""Upload security tests."""

from fastapi.testclient import TestClient


def test_upload_strips_path_traversal_filename(client: TestClient, sample_bytes: bytes) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("../../etc/passwd.md", sample_bytes, "text/markdown")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "passwd.md"
    assert ".." not in body["filename"]


def test_upload_rejects_path_only_filename(client: TestClient, sample_bytes: bytes) -> None:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("../evil.md", sample_bytes, "text/markdown")},
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "evil.md"
