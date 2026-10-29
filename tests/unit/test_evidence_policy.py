"""Evidence sufficiency policy tests."""

from backend.app.core.config import Settings
from backend.app.models.schemas import SearchResultItem
from backend.app.rag.evidence_policy import assess_retrieval_sufficiency, lexical_overlap_ratio


def _result(snippet: str, score: float = 0.2) -> SearchResultItem:
    return SearchResultItem(
        chunk_id="c1",
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
