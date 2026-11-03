"""Evidence sufficiency policy tests."""

from backend.app.core.config import Settings
from backend.app.models.schemas import SearchResultItem
from backend.app.rag.evidence_policy import (
    assess_retrieval_sufficiency,
    lexical_overlap_ratio,
    passes_lexical_evidence_support,
)


def _result(
    snippet: str,
    score: float = 0.2,
    *,
    chunk_id: str = "c1",
) -> SearchResultItem:
    return SearchResultItem(
        chunk_id=chunk_id,
        document_id="d1",
        filename="f.md",
        snippet=snippet,
        score=score,
    )


def test_lexical_overlap_rollback_question() -> None:
    snippet = "run flyway rollback -count=1 for database migration failures"
    ratio = lexical_overlap_ratio(
        "What command rolls back the database migration?",
        snippet,
    )
    assert ratio >= 0.15


def test_lexical_overlap_unrelated_question() -> None:
    snippet = "run flyway rollback -count=1 for database migration failures"
    ratio = lexical_overlap_ratio(
        "What is the capital of Mars colony Zephyr-9?",
        snippet,
    )
    assert ratio < 0.15


def test_fake_provider_rejects_unrelated() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    results = [_result("flyway rollback database migration")]
    out = assess_retrieval_sufficiency(
        "What is the capital of Mars colony Zephyr-9?",
        results,
        settings,
    )
    assert out.sufficient is False
    assert out.reason == "weak_lexical_overlap"


def test_fake_provider_accepts_relevant() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    results = [_result("flyway rollback -count=1 database migration staging")]
    out = assess_retrieval_sufficiency(
        "What command rolls back the database migration?",
        results,
        settings,
    )
    assert out.sufficient is True


def test_top_k_recovers_when_first_hit_weak_second_relevant() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    weak_first = _result(
        "Unrelated metadata about virtual environments and cache directories.",
        score=0.9,
        chunk_id="weak",
    )
    strong_second = _result(
        "This directory contains the DevOps Incident Commander project with core application files.",
        score=0.2,
        chunk_id="strong",
    )
    question = "What is the DevOps Incident Commander project directory about?"
    out = assess_retrieval_sufficiency(
        question,
        [weak_first, strong_second],
        settings,
    )
    assert out.sufficient is True
    assert out.reason == "ok"
    assert out.lexical_overlap is not None
    assert out.lexical_overlap >= 0.15


def test_shared_generic_api_token_does_not_pass_sufficiency() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    main_py_snippet = (
        "`main.py` (615 lines) - FastAPI application with all API endpoints for incident management."
    )
    question = "When should we scale API replicas for checkout latency?"
    out = assess_retrieval_sufficiency(
        question,
        [_result(main_py_snippet, score=0.5)],
        settings,
    )
    assert out.sufficient is False
    assert out.reason == "weak_lexical_overlap"
    passes, overlap, matched = passes_lexical_evidence_support(
        question,
        main_py_snippet,
        settings.evidence_min_lexical_overlap,
    )
    assert overlap >= 0.15
    assert matched == 1
    assert passes is False


def test_retrieval_order_irrelevant_first_still_insufficient() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    question = "When should we scale API replicas for checkout latency?"
    irrelevant = _result(
        "`main.py` (615 lines) - FastAPI application with all API endpoints.",
        score=0.9,
        chunk_id="irrelevant",
    )
    day7 = _result(
        "The project appears to be at Day 7 with timeline and audit trail implemented.",
        score=0.1,
        chunk_id="status",
    )
    for ordering in ([irrelevant, day7], [day7, irrelevant]):
        out = assess_retrieval_sufficiency(question, ordering, settings)
        assert out.sufficient is False
        assert out.reason == "weak_lexical_overlap"


def test_no_results_remains_insufficient() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake")
    out = assess_retrieval_sufficiency(
        "What command rolls back the database migration?",
        [],
        settings,
    )
    assert out.sufficient is False
    assert out.reason == "no_results"


def test_weak_overlap_remains_insufficient() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    out = assess_retrieval_sufficiency(
        "What is the capital of Mars colony Zephyr-9?",
        [_result("flyway rollback database migration")],
        settings,
    )
    assert out.sufficient is False
    assert out.reason == "weak_lexical_overlap"


def test_local_provider_requires_similarity_and_lexical_support() -> None:
    settings = Settings(
        EMBEDDING_PROVIDER="local",
        EVIDENCE_MIN_LEXICAL_OVERLAP=0.15,
        MIN_SIMILARITY_SCORE=0.25,
    )
    low_score = _result(
        "flyway rollback -count=1 database migration staging",
        score=0.1,
        chunk_id="low",
    )
    out = assess_retrieval_sufficiency(
        "What command rolls back the database migration?",
        [low_score],
        settings,
    )
    assert out.sufficient is False
    assert out.reason == "low_similarity"


def test_local_provider_accepts_when_second_hit_passes_gates() -> None:
    settings = Settings(
        EMBEDDING_PROVIDER="local",
        EVIDENCE_MIN_LEXICAL_OVERLAP=0.15,
        MIN_SIMILARITY_SCORE=0.25,
    )
    weak_first = _result("unrelated virtual environment cache notes", score=0.9, chunk_id="a")
    good_second = _result(
        "flyway rollback -count=1 database migration staging",
        score=0.4,
        chunk_id="b",
    )
    out = assess_retrieval_sufficiency(
        "What command rolls back the database migration?",
        [weak_first, good_second],
        settings,
    )
    assert out.sufficient is True
    assert out.reason == "ok"
    assert out.top_score == 0.4


def test_development_status_single_exact_token_exception_passes() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    status = _result(
        "The project appears to be at Day 7 with the timeline and audit trail "
        "feature already implemented.",
        score=0.47,
        chunk_id="status",
    )
    inventory = _result(
        "This directory contains the DevOps Incident Commander project with the following files.",
        score=0.39,
        chunk_id="inventory",
    )
    question = "What is the reported development status of the project?"
    out = assess_retrieval_sufficiency(question, [status, inventory], settings)
    assert out.sufficient is True
    assert out.reason == "ok"
    passes, overlap, matched = passes_lexical_evidence_support(
        question,
        status.snippet,
        settings.evidence_min_lexical_overlap,
    )
    assert matched == 1
    assert overlap >= 0.25
    assert passes is True


def test_internal_software_project_question_insufficient() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    inventory = _result(
        "This directory contains the DevOps Incident Commander project with the following files.",
        score=0.5,
    )
    question = "Is this an internal software project?"
    out = assess_retrieval_sufficiency(question, [inventory], settings)
    assert out.sufficient is False
    assert out.reason == "weak_lexical_overlap"


def test_application_architecture_question_insufficient() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    snippet = _result(
        "`main.py` (615 lines) - FastAPI application with all API endpoints.",
        score=0.5,
    )
    question = "What is the application architecture?"
    out = assess_retrieval_sufficiency(question, [snippet], settings)
    assert out.sufficient is False
    assert out.reason == "weak_lexical_overlap"


def test_status_question_without_status_evidence_insufficient() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    inventory = _result(
        "This directory contains the DevOps Incident Commander project with the following files.",
        score=0.47,
    )
    question = "What is the reported development status of the project?"
    out = assess_retrieval_sufficiency(question, [inventory], settings)
    assert out.sufficient is False
    assert out.reason == "weak_lexical_overlap"


def test_alternative_project_status_phrasing_passes_with_status_evidence() -> None:
    settings = Settings(EMBEDDING_PROVIDER="fake", EVIDENCE_MIN_LEXICAL_OVERLAP=0.15)
    status = _result(
        "The project appears to be at Day 7 with the timeline feature already implemented.",
        score=0.47,
        chunk_id="status",
    )
    question = "What is the current project status?"
    out = assess_retrieval_sufficiency(question, [status], settings)
    assert out.sufficient is True
    assert out.reason == "ok"


def test_local_provider_weak_lexical_when_similarity_ok() -> None:
    settings = Settings(
        EMBEDDING_PROVIDER="local",
        EVIDENCE_MIN_LEXICAL_OVERLAP=0.15,
        MIN_SIMILARITY_SCORE=0.25,
    )
    out = assess_retrieval_sufficiency(
        "What is the capital of Mars colony Zephyr-9?",
        [_result("flyway rollback database migration", score=0.9)],
        settings,
    )
    assert out.sufficient is False
    assert out.reason == "weak_lexical_overlap"
