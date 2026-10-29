"""Evaluation API."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_db, settings_dep
from backend.app.models.schemas import EvalRunRequest, EvalRunResponse
from backend.app.services.evaluation.runner import run_evaluation

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


@router.get("/datasets")
def list_datasets() -> dict:
    golden = _project_root() / "tests" / "golden" / "qa_pairs.json"
    return {
        "datasets": [
            {
                "name": "golden",
                "path": str(golden.relative_to(_project_root())),
                "question_count": len(json.loads(golden.read_text(encoding="utf-8"))),
            },
        ],
    }


@router.post("/runs", response_model=EvalRunResponse, status_code=201)
def create_eval_run(
    payload: EvalRunRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> EvalRunResponse:
    run = run_evaluation(
        db,
        settings,
        _project_root(),
        dataset_name=payload.dataset_name,
        top_k=payload.top_k,
    )
    return EvalRunResponse(
        run_id=run.id,
        dataset_name=run.dataset_name,
        metrics=json.loads(run.metrics_json),
        config=json.loads(run.config_json),
        created_at=run.created_at,
    )


@router.get("/runs", response_model=list[EvalRunResponse])
def list_eval_runs(db: Session = Depends(get_db)) -> list[EvalRunResponse]:
    from backend.app.database.models import EvaluationRun

    runs = db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()
    return [
        EvalRunResponse(
            run_id=r.id,
            dataset_name=r.dataset_name,
            metrics=json.loads(r.metrics_json),
            config=json.loads(r.config_json),
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=EvalRunResponse)
def get_eval_run(run_id: str, db: Session = Depends(get_db)) -> EvalRunResponse:
    from backend.app.core.exceptions import NotFoundError
    from backend.app.database.models import EvaluationRun

    run = db.get(EvaluationRun, run_id)
    if run is None:
        raise NotFoundError(f"Evaluation run {run_id} not found")
    return EvalRunResponse(
        run_id=run.id,
        dataset_name=run.dataset_name,
        metrics=json.loads(run.metrics_json),
        config=json.loads(run.config_json),
        created_at=run.created_at,
    )
