"""Evidence sufficiency checks before answer generation."""

import re
from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.models.schemas import SearchResultItem

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "what",
        "when",
        "where",
        "who",
        "how",
        "why",
        "do",
        "does",
        "did",
        "can",
        "could",
        "should",
        "would",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "with",
        "this",
        "that",
        "it",
        "be",
        "at",
        "from",
        "by",
        "about",
    },
)


def _content_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if len(t) > 1 and t not in _STOPWORDS}


def lexical_overlap_ratio(question: str, passage: str) -> float:
    """Share of question content tokens that appear in the passage."""
    q_tokens = _content_tokens(question)
    if not q_tokens:
        return 0.0
    p_tokens = _content_tokens(passage)
    if not p_tokens:
        return 0.0
    return len(q_tokens & p_tokens) / len(q_tokens)


@dataclass(frozen=True)
class SufficiencyResult:
    sufficient: bool
    reason: str
    top_score: float | None
    lexical_overlap: float | None


def assess_retrieval_sufficiency(
    question: str,
    results: list[SearchResultItem],
    settings: Settings,
) -> SufficiencyResult:
    if not results:
        return SufficiencyResult(False, "no_results", None, None)

    top = results[0]
    overlap = lexical_overlap_ratio(question, top.snippet)
    score = top.score

    if settings.embedding_provider == "local":
        if score < settings.min_similarity_score:
            return SufficiencyResult(False, "low_similarity", score, overlap)
        if overlap < settings.evidence_min_lexical_overlap:
            return SufficiencyResult(False, "weak_lexical_overlap", score, overlap)
        return SufficiencyResult(True, "ok", score, overlap)

    # Fake embeddings: scores are not semantically calibrated — require lexical support.
    min_overlap = settings.evidence_min_lexical_overlap
    if overlap < min_overlap:
        return SufficiencyResult(False, "weak_lexical_overlap", score, overlap)
    return SufficiencyResult(True, "ok", score, overlap)


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "The uploaded documents do not contain enough evidence to answer this question. "
    "Try rephrasing, uploading a relevant document, or narrowing your question."
)
