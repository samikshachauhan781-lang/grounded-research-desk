"""Research session persistence."""

import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundError
from backend.app.database.models import ResearchSession, SessionMessage, utc_now_iso
from backend.app.models.schemas import Citation


def create_session(db: Session, title: str | None = None) -> ResearchSession:
    now = utc_now_iso()
    session = ResearchSession(
        id=str(uuid.uuid4()),
        title=title or "Untitled session",
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_sessions(db: Session) -> list[tuple[ResearchSession, int]]:
    stmt = (
        select(ResearchSession, func.count(SessionMessage.id))
        .outerjoin(SessionMessage, SessionMessage.session_id == ResearchSession.id)
        .group_by(ResearchSession.id)
        .order_by(ResearchSession.updated_at.desc())
    )
    return list(db.execute(stmt).all())


def get_session(db: Session, session_id: str) -> ResearchSession:
    session = db.get(ResearchSession, session_id)
    if session is None:
        raise NotFoundError(f"Session {session_id} not found")
    return session


def delete_session(db: Session, session_id: str) -> None:
    session = get_session(db, session_id)
    db.delete(session)
    db.commit()


def list_messages(db: Session, session_id: str) -> list[SessionMessage]:
    get_session(db, session_id)
    stmt = (
        select(SessionMessage)
        .where(SessionMessage.session_id == session_id)
        .order_by(SessionMessage.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def citations_from_message(message: SessionMessage) -> list[Citation]:
    raw = json.loads(message.citations_json or "[]")
    return [Citation.model_validate(item) for item in raw]
