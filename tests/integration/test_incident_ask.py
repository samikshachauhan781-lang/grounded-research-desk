"""Integration tests for incident document ask flow."""

from pathlib import Path

from fastapi.testclient import TestClient


def test_demo_incident_ask_questions(client: TestClient, project_root: Path) -> None:
    fixture = (project_root / "tests" / "fixtures" / "demo_incident.md").read_bytes()
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("demo_incident.md", fixture, "text/markdown")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["document_id"]

    cases = [
        (
            "What caused the Payment API incident?",
            True,
            ["connection pool"],
            [],
        ),
        (
            "What happened between 10:00 AM and 10:20 AM?",
            True,
            ["10:00", "10:20", "10:15"],
            [],
        ),
        (
            "How was the incident resolved?",
            True,
            ["rolled back"],
            ["inc-2026-105"],
        ),
        (
            "What is the incident ID?",
            True,
            ["INC-2026-105"],
            [],
        ),
        (
            "What was the database password?",
            False,
            [],
            [],
        ),
    ]

    for question, expect_success, must_include, must_exclude in cases:
        response = client.post(
            "/api/v1/ask",
            json={"question": question, "document_ids": [document_id]},
        )
        assert response.status_code == 200
        body = response.json()
        if expect_success:
            assert body["insufficient_evidence"] is False, question
            answer = body["answer"].lower()
            assert "[chunk:" not in answer, question
            assert body["citations"], question
            for token in must_include:
                assert token.lower() in answer, f"{question} missing {token}"
            for token in must_exclude:
                assert token.lower() not in answer, f"{question} included {token}"
        else:
            assert body["insufficient_evidence"] is True, question
            assert body["citations"] == []
