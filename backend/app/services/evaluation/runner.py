"""Golden retrieval evaluation."""

import json
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.database.models import EvaluationRun, utc_now_iso
from backend.app.services.ingest.pipeline import ingest_upload
from backend.app.services.retrieval.search_service import search_chunks


def _load_golden_dataset(project_root: Path) -> list[dict]:
    path = project_root / "tests" / "golden" / "qa_pairs.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_evaluation(
    db: Session,
    settings: Settings,
    project_root: Path,
    dataset_name: str = "golden",
    top_k: int = 5,
) -> EvaluationRun:
    pairs = _load_golden_dataset(project_root)
    # Ensure fixture document indexed once per run
    fixture_path = project_root / "tests" / "fixtures" / "sample.md"
    fixture_bytes = fixture_path.read_bytes()
    doc = ingest_upload(db, settings, "sample.md", fixture_bytes)

    hits = 0
    precision_sum = 0.0
    reciprocal_ranks: list[float] = []
    failures: list[dict] = []

    for pair in pairs:
        question = pair["question"]
        expected = pair["expected_substring"].lower()
        response = search_chunks(db, settings, question, top_k=top_k, document_ids=[doc.id])
        matched_rank = None
        for rank, result in enumerate(response.results, start=1):
            if expected in result.snippet.lower():
                matched_rank = rank
                break
        if matched_rank is None:
            failures.append({"id": pair["id"], "question": question})
            reciprocal_ranks.append(0.0)
            continue
        hits += 1
        precision_sum += 1.0 / matched_rank
        reciprocal_ranks.append(1.0 / matched_rank)

    total = len(pairs)
    metrics = {
        "recall_at_k": hits / total if total else 0.0,
        "precision_at_k": precision_sum / total if total else 0.0,
        "mrr": sum(reciprocal_ranks) / total if total else 0.0,
        "total_questions": total,
        "failures": failures,
    }
    config = {
        "top_k": top_k,
        "embedding_provider": settings.embedding_provider,
        "embedding_model_name": settings.embedding_model_name,
        "dataset": dataset_name,
    }
    run = EvaluationRun(
        id=str(uuid.uuid4()),
        dataset_name=dataset_name,
        config_json=json.dumps(config),
        metrics_json=json.dumps(metrics),
        created_at=utc_now_iso(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
