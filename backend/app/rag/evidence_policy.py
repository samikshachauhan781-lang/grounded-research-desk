"""Evidence sufficiency checks before answer generation."""

import re
from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.models.schemas import SearchResultItem
from backend.app.rag.question_intent import asks_for_development_status

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


def content_tokens(text: str) -> set[str]:
    """Content tokens for overlap and answer-level validation."""
    return _content_tokens(text)


def lexical_overlap_ratio(question: str, passage: str) -> float:
    """Share of question content tokens that appear in the passage."""
    q_tokens = _content_tokens(question)
    if not q_tokens:
        return 0.0
    p_tokens = _content_tokens(passage)
    if not p_tokens:
        return 0.0
    return len(q_tokens & p_tokens) / len(q_tokens)


# Status-oriented single-token exception: higher overlap bar than the 0.15 floor.
_STATUS_SINGLE_TOKEN_MIN_OVERLAP = 0.25

_STATUS_PASSAGE_RE = re.compile(
    r"\b(?:already\s+)?implemented\b|\bimplementation\b|\bin\s+progress\b"
    r"|\bprogress\b|\bcompleted?\b|\bmilestone\b|\bphase\b",
    re.IGNORECASE,
)


def passage_has_status_evidence(passage: str) -> bool:
    """True when passage text indicates project/implementation status (not hardcoded answers)."""
    return bool(_STATUS_PASSAGE_RE.search(passage))


def _min_matched_content_tokens(question_token_count: int) -> int:
    """Require multiple token hits when the question has multiple content tokens."""
    if question_token_count <= 1:
        return 1
    return 2


def _question_tokens_matched_in_passage(
    q_tokens: set[str],
    p_tokens: set[str],
) -> set[str]:
    """Match question tokens to passage tokens, including conservative stem overlap."""
    matched: set[str] = set()
    for qt in q_tokens:
        if qt in p_tokens:
            matched.add(qt)
            continue
        for pt in p_tokens:
            if len(qt) >= 4 and len(pt) >= 4 and (qt in pt or pt in qt):
                matched.add(qt)
                break
        else:
            for pt in p_tokens:
                if len(qt) >= 5 and len(pt) >= 5 and qt[:5] == pt[:5]:
                    matched.add(qt)
                    break
    return matched


def passes_lexical_evidence_support(
    question: str,
    passage: str,
    min_overlap: float,
) -> tuple[bool, float, int]:
    """
    Lexical gate for a single passage.

    Returns (passes, overlap_ratio, matched_token_count).
    """
    q_tokens = _content_tokens(question)
    if not q_tokens:
        return False, 0.0, 0
    p_tokens = _content_tokens(passage)
    matched = _question_tokens_matched_in_passage(q_tokens, p_tokens)
    overlap = len(matched) / len(q_tokens)
    if overlap < min_overlap:
        return False, overlap, len(matched)
    required = _min_matched_content_tokens(len(q_tokens))
    if len(matched) >= required:
        return True, overlap, len(matched)
    if _passes_status_oriented_single_token_exception(
        question,
        passage,
        q_tokens,
        p_tokens,
        matched,
        overlap,
        min_overlap,
    ):
        return True, overlap, len(matched)
    return False, overlap, len(matched)


def _passes_status_oriented_single_token_exception(
    question: str,
    passage: str,
    q_tokens: set[str],
    p_tokens: set[str],
    matched: set[str],
    overlap: float,
    min_overlap: float,
) -> bool:
    """
    Allow one exact token hit only for status-oriented questions with status evidence.

    Stem/substring token matches alone do not qualify.
    """
    if not asks_for_development_status(question):
        return False
    if not passage_has_status_evidence(passage):
        return False
    exact_matched = q_tokens & p_tokens
    if len(exact_matched) != 1:
        return False
    if len(matched) < 1:
        return False
    return overlap >= max(min_overlap, _STATUS_SINGLE_TOKEN_MIN_OVERLAP)


@dataclass(frozen=True)
class SufficiencyResult:
    sufficient: bool
    reason: str
    top_score: float | None
    lexical_overlap: float | None


def _best_supporting_hit(
    question: str,
    results: list[SearchResultItem],
    settings: Settings,
) -> tuple[bool, str, float | None, float | None]:
    """
    Evaluate top-k hits; return (sufficient, failure_reason, best_score, best_overlap).
    """
    min_overlap = settings.evidence_min_lexical_overlap
    best_score: float | None = None
    best_overlap: float | None = None
    any_similarity_ok = False
    any_lexical_ratio_ok = False

    for item in results:
        if settings.embedding_provider == "local":
            if item.score >= settings.min_similarity_score:
                any_similarity_ok = True
            else:
                continue
        overlap_ratio = lexical_overlap_ratio(question, item.snippet)
        if overlap_ratio >= min_overlap:
            any_lexical_ratio_ok = True
        passes, overlap, _ = passes_lexical_evidence_support(
            question,
            item.snippet,
            min_overlap,
        )
        if not passes:
            continue
        if best_overlap is None or overlap > best_overlap:
            best_overlap = overlap
            best_score = item.score

    if best_overlap is not None:
        return True, "ok", best_score, best_overlap

    if settings.embedding_provider == "local" and not any_similarity_ok:
        top = results[0]
        return (
            False,
            "low_similarity",
            top.score,
            lexical_overlap_ratio(question, top.snippet),
        )

    _ = any_lexical_ratio_ok  # ratio alone does not imply support (min matched tokens)
    top = results[0]
    return (
        False,
        "weak_lexical_overlap",
        top.score,
        lexical_overlap_ratio(question, top.snippet),
    )


def assess_retrieval_sufficiency(
    question: str,
    results: list[SearchResultItem],
    settings: Settings,
) -> SufficiencyResult:
    if not results:
        return SufficiencyResult(False, "no_results", None, None)

    sufficient, reason, score, overlap = _best_supporting_hit(
        question,
        results,
        settings,
    )
    return SufficiencyResult(sufficient, reason, score, overlap)


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "The uploaded documents do not contain enough evidence to answer this question. "
    "Try rephrasing, uploading a relevant document, or narrowing your question."
)
