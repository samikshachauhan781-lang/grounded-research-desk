"""Multi-fact and multi-file synthesis regression tests."""

from backend.app.core.config import Settings
from backend.app.rag.evidence_answer import (
    synthesize_answer_from_evidence,
    validate_cited_chunk_provenance,
)
from backend.app.rag.question_intent import QuestionIntent, asks_for_development_status, detect_question_intent
from backend.app.rag.synthesis_result import SynthesisStatus

CHUNK_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CHUNK_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

INVENTORY_CHUNK = """# Current DevOps Incident Commander Project

This directory contains the DevOps Incident Commander project with the following files:

**Core Application Files:**
- `main.py` (615 lines) - FastAPI application with all API endpoints
- `models.py` (862 lines) - Pydantic data models for incident management

**Test Files:**
- `test_day7_timeline.py` (448 lines) - Timeline and audit trail tests
"""

STATUS_CHUNK = """The project appears to be at Day 7 with the timeline and audit trail feature already implemented.
"""


def _settings() -> Settings:
    return Settings()


def _single_inventory_blocks() -> list[tuple[str, str]]:
    return [(CHUNK_A, INVENTORY_CHUNK)]


def test_multiple_core_filenames_enumerated() -> None:
    result = synthesize_answer_from_evidence(
        "Which files are the core application files?",
        _single_inventory_blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "main.py" in result.answer
    assert "models.py" in result.answer
    assert result.answer.index("main.py") < result.answer.index("models.py")


def test_list_both_core_files_with_attributes() -> None:
    result = synthesize_answer_from_evidence(
        "List both core application files with their line counts and responsibilities.",
        _single_inventory_blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "615" in result.answer
    assert "862" in result.answer
    assert "FastAPI" in result.answer
    assert "Pydantic" in result.answer
    lower = result.answer.lower()
    main_pos = lower.index("main.py")
    models_pos = lower.index("models.py")
    assert "615" in result.answer[main_pos : models_pos]
    assert "862" in result.answer[models_pos:]


def test_facts_combined_across_two_chunks() -> None:
    chunk_main = (
        "**Core Application Files:**\n"
        "- `main.py` (615 lines) - FastAPI application with all API endpoints\n"
    )
    chunk_models = (
        "**Core Application Files:**\n"
        "- `models.py` (862 lines) - Pydantic data models for incident management\n"
    )
    result = synthesize_answer_from_evidence(
        "List both core application files with their line counts and responsibilities.",
        [(CHUNK_A, chunk_main), (CHUNK_B, chunk_models)],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "main.py" in result.answer and "models.py" in result.answer
    assert set(result.source_chunk_ids) == {CHUNK_A, CHUNK_B}


def test_missing_requested_file_fails_closed() -> None:
    only_main = (
        "**Core Application Files:**\n"
        "- `main.py` (615 lines) - FastAPI application with all API endpoints\n"
    )
    result = synthesize_answer_from_evidence(
        "List both core application files with their line counts and responsibilities.",
        [(CHUNK_A, only_main)],
        _settings(),
    )
    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE
    assert result.reason == "multi_fact_incomplete"


def test_all_files_request_does_not_return_first_only() -> None:
    result = synthesize_answer_from_evidence(
        "Which files are the core application files?",
        _single_inventory_blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "main.py" in result.answer and "models.py" in result.answer


def test_development_status_returns_day7_and_timeline_statement() -> None:
    question = "What is the reported development status of the project?"
    assert detect_question_intent(question) == QuestionIntent.GENERAL
    result = synthesize_answer_from_evidence(
        question,
        [(CHUNK_A, INVENTORY_CHUNK), (CHUNK_B, STATUS_CHUNK)],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    lower = result.answer.lower()
    assert "day 7" in lower
    assert "timeline" in lower
    assert "audit trail" in lower
    assert "implemented" in lower
    assert result.source_chunk_id == CHUNK_B


def test_alternative_status_phrasing_synthesis() -> None:
    question = "What is the current project status?"
    assert asks_for_development_status(question) is True
    result = synthesize_answer_from_evidence(
        question,
        [(CHUNK_A, INVENTORY_CHUNK), (CHUNK_B, STATUS_CHUNK)],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "implemented" in result.answer.lower()
    assert result.source_chunk_id == CHUNK_B


def test_status_question_without_status_chunk_fails_closed() -> None:
    from backend.app.rag.evidence_policy import assess_retrieval_sufficiency

    question = "What is the reported development status of the project?"
    settings = _settings()
    from backend.app.models.schemas import SearchResultItem

    inv = SearchResultItem(
        chunk_id=CHUNK_A,
        document_id="d1",
        filename="f.md",
        snippet=INVENTORY_CHUNK[:120],
        score=0.5,
    )
    out = assess_retrieval_sufficiency(question, [inv], settings)
    assert out.sufficient is False


def test_application_architecture_does_not_select_status_passage() -> None:
    result = synthesize_answer_from_evidence(
        "What is the application architecture?",
        [(CHUNK_A, INVENTORY_CHUNK), (CHUNK_B, STATUS_CHUNK)],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert result.source_chunk_id == CHUNK_A
    assert "day 7" not in result.answer.lower()


def test_directory_overview_general_answer() -> None:
    blocks = [(CHUNK_A, INVENTORY_CHUNK), (CHUNK_B, STATUS_CHUNK)]
    assert (
        detect_question_intent("What is the DevOps Incident Commander project directory about?")
        == QuestionIntent.GENERAL
    )
    result = synthesize_answer_from_evidence(
        "What is the DevOps Incident Commander project directory about?",
        blocks,
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "directory contains" in result.answer.lower()
    assert detect_question_intent("What is the DevOps Incident Commander project directory about?") != QuestionIntent.COMMAND


def test_command_intent_unchanged() -> None:
    assert detect_question_intent("What command should I run?") == QuestionIntent.COMMAND


def test_resolution_intent_unchanged() -> None:
    assert (
        detect_question_intent("Why was the incident resolved?")
        == QuestionIntent.RESOLUTION
    )


def test_sensitive_password_still_blocked() -> None:
    result = synthesize_answer_from_evidence(
        "What was the database password?",
        _single_inventory_blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE


def test_multi_chunk_provenance_accepts_supporting_citation() -> None:
    chunk_main = (
        "**Core Application Files:**\n"
        "- `main.py` (615 lines) - FastAPI application with all API endpoints\n"
    )
    chunk_models = (
        "**Core Application Files:**\n"
        "- `models.py` (862 lines) - Pydantic data models for incident management\n"
    )
    blocks = [(CHUNK_A, chunk_main), (CHUNK_B, chunk_models)]
    question = "List both core application files with their line counts and responsibilities."
    result = synthesize_answer_from_evidence(question, blocks, _settings())
    assert result.status == SynthesisStatus.SUCCESS
    ok, reason = validate_cited_chunk_provenance(
        question,
        result.answer,
        CHUNK_A,
        blocks,
        _settings(),
    )
    assert ok is True, reason
