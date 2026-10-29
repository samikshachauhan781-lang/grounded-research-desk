"""Session persistence via ask API."""

from fastapi.testclient import TestClient


def test_ask_persists_messages_when_session_id_provided(
    client: TestClient,
    sample_bytes: bytes,
) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("sample.md", sample_bytes, "text/markdown")},
    )
    document_id = upload.json()["document_id"]

    session = client.post("/api/v1/sessions", json={"title": "Demo session"})
    assert session.status_code == 201
    session_id = session.json()["session_id"]

    ask = client.post(
        "/api/v1/ask",
        json={
            "question": "What command rolls back the database migration?",
            "document_ids": [document_id],
            "session_id": session_id,
        },
    )
    assert ask.status_code == 200
    assert ask.json()["session_id"] == session_id

    messages = client.get(f"/api/v1/sessions/{session_id}/messages")
    assert messages.status_code == 200
    assert len(messages.json()) == 1
    assert messages.json()[0]["question"].startswith("What command")
