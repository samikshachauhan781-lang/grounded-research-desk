"""SQLAlchemy engine and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.app.core.config import Settings

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def configure_database(settings: Settings) -> None:
    global engine, SessionLocal
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_database() -> None:
    from backend.app.database import models  # noqa: F401

    if engine is None:
        msg = "Database not configured"
        raise RuntimeError(msg)
    Base.metadata.create_all(bind=engine)
