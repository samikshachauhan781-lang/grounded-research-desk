"""Ollama generation provider tests (HTTP mocked)."""

from unittest.mock import MagicMock, patch

import httpx

from backend.app.core.config import Settings
from backend.app.core.exceptions import LLMTimeoutError
from backend.app.providers.llm import OllamaGenerationProvider
from backend.app.rag.synthesis_result import SynthesisStatus


def test_ollama_parses_chunk_citations_from_response() -> None:
    settings = Settings(
        LLM_PROVIDER="ollama",
        OLLAMA_BASE_URL="http://127.0.0.1:11434",
        OLLAMA_MODEL="llama3.2",
    )
    chunk_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    provider = OllamaGenerationProvider(settings)
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "response": (
            f"The file is `test_day7_timeline.py`. It has the tests. [chunk:{chunk_id}]"
        ),
    }

    with patch("httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.return_value = mock_response
        client_cls.return_value = client

        result = provider.generate_answer(
            "Which file contains all the tests for the new timeline functionality?",
            [
                (
                    chunk_id,
                    "The `test_day7_timeline.py` file contains all the tests "
                    "for the new timeline functionality.",
                ),
            ],
            timeout_seconds=30,
        )

    assert result.status == SynthesisStatus.SUCCESS
    assert result.source_chunk_id == chunk_id
    assert "test_day7_timeline" in result.answer
    posted = client.post.call_args
    assert posted is not None
    prompt = posted.kwargs["json"]["prompt"]
    assert "Answer the user's question directly" in prompt


def test_ollama_missing_citation_is_insufficient_not_fallback() -> None:
    settings = Settings(LLM_PROVIDER="ollama")
    chunk_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    provider = OllamaGenerationProvider(settings)
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "response": "The file is test_day7_timeline.py with no citation tag.",
    }

    with patch("httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.return_value = mock_response
        client_cls.return_value = client

        result = provider.generate_answer(
            "Which file has the tests?",
            [(chunk_id, "evidence text")],
            timeout_seconds=30,
        )

    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE
    assert result.reason == "missing_chunk_citation"
    assert result.source_chunk_id is None


def test_ollama_timeout_raises() -> None:
    settings = Settings(LLM_PROVIDER="ollama")
    provider = OllamaGenerationProvider(settings)

    with patch("httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.side_effect = httpx.TimeoutException("slow")
        client_cls.return_value = client

        try:
            provider.generate_answer("q", [("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "text")], timeout_seconds=1)
            raised = False
        except LLMTimeoutError:
            raised = True

    assert raised


def test_ollama_wrong_chunk_tag_returns_insufficient() -> None:
    chunk_a = "11111111-1111-1111-1111-111111111111"
    chunk_b = "22222222-2222-2222-2222-222222222222"
    settings = Settings(LLM_PROVIDER="ollama")
    provider = OllamaGenerationProvider(settings)
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "response": (
            "The file is `test_day7_timeline.py`. It contains the timeline tests. "
            f"[chunk:{chunk_a}]"
        ),
    }

    with patch("httpx.Client") as client_cls:
        client = MagicMock()
        client.__enter__.return_value = client
        client.__exit__.return_value = None
        client.post.return_value = mock_response
        client_cls.return_value = client

        result = provider.generate_answer(
            "Which file contains all the tests for the new timeline functionality?",
            [
                (chunk_a, "Database migrations use flyway rollback on staging servers."),
                (
                    chunk_b,
                    "The `test_day7_timeline.py` file contains all the tests "
                    "for the new timeline functionality.",
                ),
            ],
            timeout_seconds=30,
        )

    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE
    assert result.reason == "citation_chunk_mismatch"
    assert result.source_chunk_id is None
