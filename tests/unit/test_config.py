"""Settings and environment configuration tests."""

import pytest

from backend.app.core.config import Settings, get_settings


def test_settings_defaults_match_documentation() -> None:
    settings = Settings()
    assert settings.app_name == "grounded-research-desk"
    assert settings.api_port == 8000
    assert settings.api_prefix == "/api/v1"
    assert settings.llm_provider == "mock"
    assert settings.agent_enabled is False


def test_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "custom-app")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "10")
    settings = Settings()
    assert settings.app_name == "custom-app"
    assert settings.retrieval_top_k == 10


def test_settings_rejects_invalid_chunk_overlap() -> None:
    with pytest.raises(ValueError, match="CHUNK_OVERLAP_CHARS"):
        Settings(CHUNK_SIZE_CHARS=100, CHUNK_OVERLAP_CHARS=100)


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
    get_settings.cache_clear()


def test_allowed_extensions_parsed() -> None:
    settings = Settings(ALLOWED_UPLOAD_EXTENSIONS=".txt, .md")
    assert settings.allowed_extensions_list == [".txt", ".md"]


def test_log_level_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")
    settings = Settings()
    assert settings.log_level == "DEBUG"
