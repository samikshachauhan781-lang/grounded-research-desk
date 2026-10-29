"""Ask / RAG API."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.dependencies import get_db, settings_dep
from backend.app.models.schemas import AskRequest, AskResponse
from backend.app.services.generation.ask_service import ask_question

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(settings_dep),
) -> AskResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    session_id = payload.session_id or payload.conversation_id
    return ask_question(
        db,
        settings,
        question=payload.question,
        request_id=request_id,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
        session_id=session_id,
    )
