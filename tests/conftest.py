"""Shared pytest fixtures."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.core.dependencies import get_db
from backend.app.database import session as db_session
from backend.app.main import create_app
from backend.app.providers.embedding import FakeEmbeddingProvider


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        APP_NAME="grounded-research-desk-test",
        APP_ENV="development",
        LOG_LEVEL="WARNING",
        DATABASE_URL=f"sqlite:///{db_path}",
        UPLOAD_DIR=str(upload_dir),
        DATA_DIR=str(tmp_path),
        EMBEDDING_PROVIDER="fake",
        LLM_PROVIDER="mock",
        AGENT_ENABLED=True,
        MIN_SIMILARITY_SCORE=0.0,
    )


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    get_settings.cache_clear()
    app = create_app(settings=test_settings)
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture
def db_session(test_settings: Settings) -> Generator[Session, None, None]:
    get_settings.cache_clear()
    db_session.configure_database(test_settings)
    app = create_app(settings=test_settings)
    session = db_session.SessionLocal()
    try:
        yield session
    finally:
        session.close()
        get_settings.cache_clear()


@pytest.fixture
def fake_embedder(test_settings: Settings) -> FakeEmbeddingProvider:
    return FakeEmbeddingProvider(test_settings)


@pytest.fixture
def sample_bytes(project_root: Path) -> bytes:
    return (project_root / "tests" / "fixtures" / "sample.md").read_bytes()
