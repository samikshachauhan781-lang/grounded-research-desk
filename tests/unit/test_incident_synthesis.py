"""Incident-style document synthesis tests."""

import re

from backend.app.core.config import Settings
from backend.app.rag.evidence_answer import (
    SYNTHESIS_MAX_CHUNK_CHARS,
    clip_chunk_text_for_synthesis,
    strip_chunk_citation_tags,
    synthesize_answer_from_evidence,
    timeline_spans_multiple_chunks,
    validate_cited_chunk_provenance,
)
from backend.app.rag.question_intent import QuestionIntent, detect_question_intent
from backend.app.rag.synthesis_result import SynthesisStatus

_CHUNK_TAG = re.compile(r"\[chunk:[a-f0-9-]{36}\]", re.IGNORECASE)

DEMO_INCIDENT = """# Payment API Incident

Incident ID: INC-2026-105
Service: Payment API

## Root cause

The new deployment increased database connection usage, exhausting the database connection pool.

## Timeline

- 10:00 AM — New deployment started.
- 10:05 AM — API error rate increased.
- 10:10 AM — Database connection pool exhaustion detected.
- 10:15 AM — Deployment rollback initiated.
- 10:20 AM — API service recovered.

## Resolution

The deployment was rolled back, and the API recovered after database connections were released.
"""

CHUNK_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _settings() -> Settings:
    return Settings()


def _blocks(text: str = DEMO_INCIDENT) -> list[tuple[str, str]]:
    return [(CHUNK_ID, text)]


def assert_no_visible_chunk_tag(answer: str) -> None:
    assert not _CHUNK_TAG.search(answer)


def test_root_cause_extraction() -> None:
    result = synthesize_answer_from_evidence(
        "What caused the Payment API incident?",
        _blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "connection pool" in result.answer.lower()
    assert "service: payment api" not in result.answer.lower()
    assert_no_visible_chunk_tag(result.answer)


def test_resolution_extraction() -> None:
    result = synthesize_answer_from_evidence(
        "How was the incident resolved?",
        _blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "rolled back" in result.answer.lower()
    assert "inc-2026-105" not in result.answer.lower()
    assert_no_visible_chunk_tag(result.answer)


def test_why_was_resolved_returns_resolution_text_not_root_cause() -> None:
    assert detect_question_intent("Why was the incident resolved?") == QuestionIntent.RESOLUTION
    result = synthesize_answer_from_evidence(
        "Why was the incident resolved?",
        _blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "rolled back" in result.answer.lower()
    assert "connection pool" not in result.answer.lower()


def test_timeline_single_chunk_complete_success() -> None:
    result = synthesize_answer_from_evidence(
        "What happened between 10:00 AM and 10:20 AM?",
        _blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert result.answer.count("- 10:") >= 5


CHUNK_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _timeline_chunk(*lines: str) -> str:
    body = "\n".join(f"- {line}" for line in lines)
    return f"## Timeline\n\n{body}\n"


def test_timeline_split_across_two_chunks_fails_closed() -> None:
    blocks = [
        (
            CHUNK_ID,
            _timeline_chunk("10:00 AM — Event one.", "10:05 AM — Event two."),
        ),
        (
            CHUNK_B,
            _timeline_chunk("10:10 AM — Event three.", "10:15 AM — Event four."),
        ),
    ]
    question = "What happened between 10:00 AM and 10:15 AM?"
    assert timeline_spans_multiple_chunks(question, blocks) is True
    result = synthesize_answer_from_evidence(question, blocks, _settings())
    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE
    assert result.reason == "timeline_spans_multiple_chunks"
    ok, reason = validate_cited_chunk_provenance(
        question,
        "- 10:00 AM — Event one.",
        CHUNK_ID,
        blocks,
        _settings(),
    )
    assert ok is False
    assert reason == "cited_insufficient_evidence"


def test_timeline_out_of_range_chunk_ignored_single_chunk_success() -> None:
    in_range_doc = DEMO_INCIDENT
    extra_only = _timeline_chunk("10:25 AM — Post-incident review scheduled.")
    blocks = [(CHUNK_ID, in_range_doc), (CHUNK_B, extra_only)]
    question = "What happened between 10:05 AM and 10:15 AM?"
    assert timeline_spans_multiple_chunks(question, blocks) is False
    result = synthesize_answer_from_evidence(question, blocks, _settings())
    assert result.status == SynthesisStatus.SUCCESS
    assert "10:05" in result.answer
    assert "10:25" not in result.answer


def test_timeline_no_events_insufficient() -> None:
    result = synthesize_answer_from_evidence(
        "What happened between 10:00 AM and 10:20 AM?",
        [(CHUNK_ID, "## Summary\n\nNo timeline here.")],
        _settings(),
    )
    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE


def test_credential_rotation_policy_answer_allowed() -> None:
    doc = (
        "## Credential management\n\n"
        "All service credentials rotate every 90 days per the credential rotation policy."
    )
    result = synthesize_answer_from_evidence(
        "What is the credential rotation policy?",
        [(CHUNK_ID, doc)],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "90 days" in result.answer


def test_timeline_all_five_events_in_order() -> None:
    result = synthesize_answer_from_evidence(
        "What happened between 10:00 AM and 10:20 AM?",
        _blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert result.answer.index("10:00") < result.answer.index("10:05")
    assert result.answer.index("10:05") < result.answer.index("10:10")
    assert result.answer.index("10:10") < result.answer.index("10:15")
    assert result.answer.index("10:15") < result.answer.index("10:20")
    assert result.answer.count("—") >= 5 or result.answer.count("- 10:") >= 5
    assert_no_visible_chunk_tag(result.answer)


def test_timeline_range_excludes_outside_events() -> None:
    narrow = DEMO_INCIDENT.replace(
        "- 10:25 AM — Post-incident review scheduled.",
        "",
    )
    result = synthesize_answer_from_evidence(
        "What happened between 10:05 AM and 10:15 AM?",
        _blocks(narrow),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "10:05" in result.answer
    assert "10:10" in result.answer
    assert "10:15" in result.answer
    assert "10:00" not in result.answer
    assert "10:20" not in result.answer


def test_metadata_incident_id() -> None:
    result = synthesize_answer_from_evidence(
        "What is the incident ID?",
        _blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "INC-2026-105" in result.answer
    assert_no_visible_chunk_tag(result.answer)


def test_unsupported_password_question_fails_closed() -> None:
    result = synthesize_answer_from_evidence(
        "What was the database password?",
        _blocks(),
        _settings(),
    )
    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE


def test_general_factual_still_grounded() -> None:
    result = synthesize_answer_from_evidence(
        "What command rolls back the database migration?",
        [
            (
                CHUNK_ID,
                "Use flyway rollback -count=1 when migration fails.",
            ),
        ],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "flyway rollback" in result.answer.lower()


def test_citation_provenance_matches_source_chunk() -> None:
    result = synthesize_answer_from_evidence(
        "What caused the Payment API incident?",
        _blocks(),
        _settings(),
    )
    assert result.source_chunk_id == CHUNK_ID
    ok, _ = validate_cited_chunk_provenance(
        "What caused the Payment API incident?",
        result.answer,
        CHUNK_ID,
        _blocks(),
        _settings(),
    )
    assert ok is True


def test_wrong_citation_chunk_rejected() -> None:
    other = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    result = synthesize_answer_from_evidence(
        "What caused the Payment API incident?",
        _blocks(),
        _settings(),
    )
    ok, reason = validate_cited_chunk_provenance(
        "What caused the Payment API incident?",
        result.answer,
        other,
        _blocks(),
        _settings(),
    )
    assert ok is False
    assert reason == "citation_not_in_context"


def test_full_chunk_available_to_synthesis_via_clip() -> None:
    padded = DEMO_INCIDENT + ("X" * (SYNTHESIS_MAX_CHUNK_CHARS + 500))
    clipped = clip_chunk_text_for_synthesis(padded)
    assert len(clipped) == SYNTHESIS_MAX_CHUNK_CHARS
    result = synthesize_answer_from_evidence(
        "How was the incident resolved?",
        [(CHUNK_ID, clipped)],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert "rolled back" in result.answer.lower()


def test_strip_chunk_citation_tags_helper() -> None:
    tagged = "Answer text [chunk:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee]"
    assert strip_chunk_citation_tags(tagged) == "Answer text"
