"""Agent research API."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_db, settings_dep
from backend.app.models.schemas import ResearchRequest, ResearchResponse
from backend.app.agents.orchestrator import run_research

router = APIRouter(tags=["agent"])


@router.post("/research", response_model=ResearchResponse)
def research(
    payload: ResearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> ResearchResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return run_research(
        db,
        settings,
        goal=payload.goal,
        request_id=request_id,
        document_ids=payload.document_ids or None,
    )


@router.post("/agent/runs", response_model=ResearchResponse)
def agent_runs_alias(
    payload: ResearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> ResearchResponse:
    return research(payload, request, db, settings)
