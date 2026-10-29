"""Evaluation integration test."""

from fastapi.testclient import TestClient


def test_evaluation_run_metrics(client: TestClient) -> None:
    response = client.post("/api/v1/evaluations/runs", json={"dataset_name": "golden", "top_k": 5})
    assert response.status_code == 201
    metrics = response.json()["metrics"]
    assert metrics["total_questions"] >= 1
    assert metrics["recall_at_k"] == 1.0
