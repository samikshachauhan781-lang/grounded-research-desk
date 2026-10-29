"""Research session API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_db
from backend.app.models.schemas import (
    SessionCreate,
    SessionMessageResponse,
    SessionResponse,
)
from backend.app.services import sessions as session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionResponse:
    session = session_service.create_session(db, payload.title)
    return SessionResponse(
        session_id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_db)) -> list[SessionResponse]:
    rows = session_service.list_sessions(db)
    return [
        SessionResponse(
            session_id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=int(count),
        )
        for s, count in rows
    ]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionResponse:
    session = session_service.get_session(db, session_id)
    messages = session_service.list_messages(db, session_id)
    return SessionResponse(
        session_id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(messages),
    )


@router.get("/{session_id}/messages", response_model=list[SessionMessageResponse])
def get_messages(session_id: str, db: Session = Depends(get_db)) -> list[SessionMessageResponse]:
    messages = session_service.list_messages(db, session_id)
    return [
        SessionMessageResponse(
            message_id=m.id,
            question=m.question,
            answer=m.answer,
            citations=session_service.citations_from_message(m),
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str, db: Session = Depends(get_db)) -> None:
    session_service.delete_session(db, session_id)
