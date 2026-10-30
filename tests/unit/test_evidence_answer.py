"""Unit tests for evidence-based mock answer synthesis."""

from backend.app.core.config import Settings
from backend.app.rag.evidence_answer import (
    format_direct_answer,
    passage_supports_question,
    synthesize_answer_from_evidence,
    validate_cited_chunk_provenance,
)
from backend.app.rag.synthesis_result import SynthesisStatus


def _settings() -> Settings:
    return Settings()


def test_file_question_extracts_backtick_filename() -> None:
    passage = (
        "The `test_day7_timeline.py` file contains all the tests "
        "for the new timeline functionality."
    )
    answer = format_direct_answer(
        "Which file contains all the tests for the new timeline functionality?",
        passage,
    )
    assert "test_day7_timeline.py" in answer
    assert "timeline functionality" in answer.lower()
    assert "DAY7_CHANGES_SUMMARY" not in answer


def test_file_question_filename_inside_code_fence() -> None:
    chunk = """Intro paragraph that does not name the test module.

```text
test_day7_timeline.py
```
"""
    chunk_id = "fence-chunk-id-0000-0000-000000000001"
    result = synthesize_answer_from_evidence(
        "Which file contains all the tests for the new timeline functionality?",
        [(chunk_id, chunk)],
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert result.source_chunk_id == chunk_id
    assert "test_day7_timeline.py" in result.answer
    assert f"[chunk:{chunk_id}]" in result.answer


def test_command_question_from_code_line() -> None:
    passage = "flyway rollback -count=1"
    answer = format_direct_answer(
        "What command rolls back the database migration?",
        passage,
    )
    assert "flyway rollback" in answer.lower()


def test_synthesize_includes_chunk_citation_tag() -> None:
    chunk_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    blocks = [
        (
            chunk_id,
            "The `test_day7_timeline.py` file contains all the tests "
            "for the new timeline functionality.",
        ),
    ]
    result = synthesize_answer_from_evidence(
        "Which file contains all the tests for the new timeline functionality?",
        blocks,
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert f"[chunk:{chunk_id}]" in result.answer
    assert result.source_chunk_id == chunk_id
    assert "test_day7_timeline.py" in result.answer
    assert "Based on the retrieved evidence" not in result.answer


def test_synthesize_picks_passage_with_higher_overlap() -> None:
    low_id = "11111111-1111-1111-1111-111111111111"
    high_id = "22222222-2222-2222-2222-222222222222"
    blocks = [
        (low_id, "DAY7_CHANGES_SUMMARY.md (394 lines) - Day 7 implementation documentation."),
        (
            high_id,
            "The `test_day7_timeline.py` file contains all the tests "
            "for the new timeline functionality.",
        ),
    ]
    result = synthesize_answer_from_evidence(
        "Which file contains all the tests for the new timeline functionality?",
        blocks,
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert result.source_chunk_id == high_id
    assert "test_day7_timeline.py" in result.answer
    assert f"[chunk:{high_id}]" in result.answer


def test_vague_file_question_returns_insufficient() -> None:
    chunk_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    vague = (
        "This document describes timeline functionality and tests in general "
        "for the new feature."
    )
    result = synthesize_answer_from_evidence(
        "Which file contains all the tests for the new timeline functionality?",
        [(chunk_id, vague)],
        _settings(),
    )
    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE
    assert result.reason == "file_question_no_filename"
    assert result.source_chunk_id is None
    assert result.answer == ""


def test_metadata_only_passage_insufficient_for_file_question() -> None:
    meta_id = "11111111-1111-1111-1111-111111111111"
    meta = "DAY7_CHANGES_SUMMARY.md (394 lines) - Day 7 implementation documentation."
    supported, reason = passage_supports_question(
        "Which file contains all the tests for the new timeline functionality?",
        meta,
        _settings(),
    )
    assert supported is False
    assert reason == "passage_lexical_overlap"

    result = synthesize_answer_from_evidence(
        "Which file contains all the tests for the new timeline functionality?",
        [(meta_id, meta)],
        _settings(),
    )
    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE


def test_second_chunk_wins_citation_provenance() -> None:
    chunk_a = "11111111-1111-1111-1111-111111111111"
    chunk_b = "22222222-2222-2222-2222-222222222222"
    blocks = [
        (chunk_a, "DAY7_CHANGES_SUMMARY.md (394 lines) - header only."),
        (
            chunk_b,
            "The `test_day7_timeline.py` file contains all the tests "
            "for the new timeline functionality.",
        ),
    ]
    result = synthesize_answer_from_evidence(
        "Which file contains all the tests for the new timeline functionality?",
        blocks,
        _settings(),
    )
    assert result.status == SynthesisStatus.SUCCESS
    assert result.source_chunk_id == chunk_b
    assert f"[chunk:{chunk_b}]" in result.answer
    assert f"[chunk:{chunk_a}]" not in result.answer


def test_validate_cited_chunk_provenance_rejects_mismatched_tag() -> None:
    chunk_a = "11111111-1111-1111-1111-111111111111"
    chunk_b = "22222222-2222-2222-2222-222222222222"
    blocks = [
        (chunk_a, "Database migrations use flyway rollback on staging servers."),
        (
            chunk_b,
            "The `test_day7_timeline.py` file contains all the tests "
            "for the new timeline functionality.",
        ),
    ]
    question = "Which file contains all the tests for the new timeline functionality?"
    answer = (
        "The file is `test_day7_timeline.py`. It contains the timeline tests. "
        f"[chunk:{chunk_a}]"
    )
    ok, reason = validate_cited_chunk_provenance(question, answer, chunk_a, blocks, _settings())
    assert ok is False
    assert reason == "citation_chunk_mismatch"


def test_validate_cited_chunk_provenance_accepts_matching_tag() -> None:
    chunk_b = "22222222-2222-2222-2222-222222222222"
    blocks = [
        (
            "11111111-1111-1111-1111-111111111111",
            "DAY7_CHANGES_SUMMARY.md (394 lines) - header only.",
        ),
        (
            chunk_b,
            "The `test_day7_timeline.py` file contains all the tests "
            "for the new timeline functionality.",
        ),
    ]
    question = "Which file contains all the tests for the new timeline functionality?"
    answer = (
        "The file is `test_day7_timeline.py`. It contains all the tests "
        f"for the new timeline functionality. [chunk:{chunk_b}]"
    )
    ok, reason = validate_cited_chunk_provenance(question, answer, chunk_b, blocks, _settings())
    assert ok is True
    assert reason == "ok"
