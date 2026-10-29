"""FastAPI dependency providers."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.database import session as db_session


def get_db() -> Generator[Session, None, None]:
    if db_session.SessionLocal is None:
        msg = "Database not configured"
        raise RuntimeError(msg)
    db = db_session.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def settings_dep() -> Settings:
    return get_settings()
